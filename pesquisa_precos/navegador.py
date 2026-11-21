# language: Python 3.11+, file: pesquisa_precos/navegador.py
from __future__ import annotations

import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .config import Config

# Remove as digitais mais óbvias do webdriver. Não é bala de prata: sites com
# detecção séria (Cloudflare Turnstile, DataDome) ainda pedem perfil real,
# headless=False e um IP que já tenha navegado.
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = window.chrome || {runtime: {}};
const _query = navigator.permissions && navigator.permissions.query;
if (_query) {
  navigator.permissions.query = (p) => (
    p && p.name === 'notifications'
      ? Promise.resolve({state: Notification.permission})
      : _query(p)
  );
}
"""


def criar_navegador(cfg: Config) -> webdriver.Chrome:
    opcoes = Options()
    binario = cfg.localizar_navegador()
    if binario:
        opcoes.binary_location = binario

    opcoes.add_argument(f"--user-agent={cfg.user_agent}")
    opcoes.add_argument("--disable-blink-features=AutomationControlled")
    opcoes.add_argument("--disable-infobars")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--no-first-run")
    opcoes.add_argument("--no-default-browser-check")
    opcoes.add_argument("--lang=pt-BR")
    opcoes.add_argument("--window-size=1440,960")
    opcoes.add_experimental_option(
        "excludeSwitches", ["enable-automation", "enable-logging"]
    )
    opcoes.add_experimental_option("useAutomationExtension", False)
    opcoes.add_experimental_option(
        "prefs",
        {
            "intl.accept_languages": "pt-BR,pt,en-US,en",
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        },
    )

    if cfg.headless:
        opcoes.add_argument("--headless=new")
    if cfg.perfil_dir:
        Path(cfg.perfil_dir).mkdir(parents=True, exist_ok=True)
        opcoes.add_argument(f"--user-data-dir={Path(cfg.perfil_dir).resolve()}")

    try:
        driver = webdriver.Chrome(options=opcoes)
    except WebDriverException as e:
        raise RuntimeError(
            "Não consegui subir o Chrome/Brave. Confira se o navegador está "
            "instalado e se o Selenium Manager conseguiu baixar o chromedriver.\n"
            f"Detalhe: {e}"
        ) from e

    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument", {"source": STEALTH_JS}
        )
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": cfg.user_agent,
                "acceptLanguage": "pt-BR,pt;q=0.9,en-US;q=0.8",
                "platform": "Win32",
            },
        )
    except WebDriverException:
        pass  # Brave antigo pode recusar um dos comandos; segue sem eles

    driver.set_page_load_timeout(cfg.timeout_pagina)
    driver.set_script_timeout(30)
    return driver


# ---------------------------------------------------------------- espera


def abrir(driver: webdriver.Chrome, url: str, timeout: int = 40) -> bool:
    try:
        driver.get(url)
        return True
    except TimeoutException:
        # load travado em anúncio: o DOM normalmente já está utilizável
        try:
            driver.execute_script("window.stop();")
        except WebDriverException:
            pass
        return False


def esperar_css(driver: webdriver.Chrome, seletor: str, timeout: int = 15) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, seletor)
        )
        return True
    except TimeoutException:
        return False


def esperar_texto(driver: webdriver.Chrome, seletor: str, timeout: int = 15) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: any(
                e.text.strip() for e in d.find_elements(By.CSS_SELECTOR, seletor)
            )
        )
        return True
    except TimeoutException:
        return False


def rolar(driver: webdriver.Chrome, passos: int = 4, pausa: float = 0.35) -> None:
    """Dispara o lazy-load das imagens e dos cartões que nascem no scroll."""
    for i in range(1, passos + 1):
        driver.execute_script(
            f"window.scrollTo(0, document.body.scrollHeight*{i / passos});"
        )
        time.sleep(pausa)
    driver.execute_script("window.scrollTo(0, 0);")


def salvar_debug(driver: webdriver.Chrome, cfg: Config, nome: str) -> Path:
    cfg.dir_debug.mkdir(parents=True, exist_ok=True)
    destino = cfg.dir_debug / f"{nome}_{time.strftime('%Y%m%d_%H%M%S')}.html"
    destino.write_text(driver.page_source, encoding="utf-8", errors="ignore")
    return destino


MARCADORES_BLOQUEIO = {
    "suspicious-traffic": "página de tráfego suspeito",
    "digite os caracteres": "captcha",
    "api-services-support@amazon.com": "captcha da Amazon",
    "não é possível acessar a página": "bloqueio por IP",
    "unusual traffic": "tráfego incomum",
    "robot check": "verificação anti-robô",
}


def detectar_bloqueio(driver: webdriver.Chrome) -> str | None:
    """Reconhece as páginas de verificação que os marketplaces servem no lugar do resultado."""
    try:
        fonte = driver.page_source[:300_000].lower()
    except WebDriverException:
        return None
    for marcador, motivo in MARCADORES_BLOQUEIO.items():
        if marcador in fonte:
            return motivo
    return None


# ---------------------------------------------------------------- coleta


def coletar_cartoes(driver: webdriver.Chrome, js: str) -> list[dict]:
    """Executa um coletor JS que devolve [{titulo, preco, parcelas, texto, link, imagem}]."""
    try:
        bruto = driver.execute_script(js) or []
    except WebDriverException:
        return []
    saida: list[dict] = []
    for item in bruto:
        if not isinstance(item, dict):
            continue
        limpo = {k: (v if isinstance(v, str) else "") for k, v in item.items()}
        if limpo.get("titulo"):
            saida.append(limpo)
    return saida


def detalhar_parcelamento(driver: webdriver.Chrome, url: str, timeout: int = 12) -> str:
    """Abre o anúncio numa aba nova e devolve o trecho que fala de parcelas.

    Sites de comparação (Buscapé) mostram preço no cartão e parcelamento só na
    página do produto. Custa uma requisição por oferta — use com --detalhar.
    """
    if not url:
        return ""
    aba_original = driver.current_window_handle
    try:
        driver.execute_script("window.open(arguments[0], '_blank');", url)
        time.sleep(0.4)
        driver.switch_to.window(driver.window_handles[-1])
        WebDriverWait(driver, timeout).until(
            lambda d: (
                d.execute_script(
                    "return document.body ? document.body.innerText.length : 0"
                )
                > 400
            )
        )
        texto = driver.execute_script("return document.body.innerText;") or ""
        return texto
    except (TimeoutException, WebDriverException):
        return ""
    finally:
        try:
            if driver.current_window_handle != aba_original:
                driver.close()
            driver.switch_to.window(aba_original)
        except WebDriverException:
            pass
