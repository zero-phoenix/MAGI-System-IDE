"""
La puerta del navegador: se abre solo si tú la abres, y sin ventana.

QUÉ SE ESTÁ TOCANDO
===================
Una de las cuatro invariantes que Naoko verifica. Conviene ser exacto sobre qué
prohibía `no_browser` y por qué: **no existe porque los navegadores sean
malos**, sino porque g4f abría el Chrome DEL USUARIO, sin avisar, en mitad de
una petición. Le secuestraba la sesión y a veces se quedaba colgado.

El problema era la apertura **invisible y no consentida**.

Seis proveedores —Claude, OpenaiChat, Copilot, LMArena, Cloudflare, DeepInfra—
no pueden responder sin una sesión autenticada. Cerrarles la puerta para
siempre es renunciar a ellos; abrirla del todo es volver al fallo.

La invariante pasa de «no se abre ningún navegador» a **«ninguno se abre sin
que tú lo pidas, ninguno usa tu perfil, ninguno muestra ventana, y todos quedan
registrados»**. Es más fuerte, no más débil: la primera se cumplía por no
poder, y esta se cumple pudiendo.

Cada una de esas cuatro condiciones tiene su test aquí. Un permiso de seguridad
que solo está documentado no es un permiso.
"""
from __future__ import annotations

import time

import pytest

from magi.core import no_browser, sesion_web


@pytest.fixture(autouse=True)
def sin_permiso():
    """Cada test arranca sin permiso. El estado por defecto es el cerrado."""
    sesion_web.revocar_permiso()
    yield
    sesion_web.revocar_permiso()


@pytest.fixture()
def datos_propios():
    """
    Directorio de datos aislado del test en curso.

    Se apoya en la fixture `isolated_data_dir` de conftest (autouse), que ya
    redirige MAGI_DATA_DIR y limpia la caché de `paths`. Sustituir `data_dir`
    con un lambda propio rompía ese teardown —espera una función cacheada— y
    dejaba seis tests en error por la fixture, no por el código.
    """
    from magi.core.paths import data_dir
    return data_dir()


# ------------------------------------------------- 1. cerrado por defecto

def test_sin_permiso_no_se_abre_nada(monkeypatch):
    # Motor presente y simulado: así el ÚNICO motivo posible para negarse es
    # el permiso, que es lo que este test dice comprobar. Sin esto, en el CI
    # —sin navegador— pasaba por la otra rama y no comprobaba el permiso.
    monkeypatch.setattr(sesion_web, "disponible", lambda: (True, "simulado"))

    puede, motivo = sesion_web.puede_abrir()
    assert puede is False
    assert "no hay permiso vigente" in motivo


def test_el_cortafuegos_sigue_bloqueando_sin_permiso():
    """
    La comprobación que importa: que la grieta esté CERRADA por defecto.

    Si esto falla, se ha reintroducido el fallo original — un navegador
    abriéndose sin que nadie lo pidiera.
    """
    no_browser.install()
    import subprocess
    with pytest.raises(no_browser.BrowserBlocked):
        subprocess.Popen(["chrome.exe", "--headless"])


def test_el_bloqueo_queda_anotado_como_violacion():
    no_browser.install()
    import subprocess
    antes = no_browser.violation_count()
    with pytest.raises(no_browser.BrowserBlocked):
        subprocess.Popen(["msedge.exe"])
    assert no_browser.violation_count() > antes


# ------------------------------------------------- 2. el permiso caduca

def test_el_permiso_caduca_solo():
    """
    Un permiso que no caduca deja de ser un permiso y pasa a ser una
    configuración: se concede una vez, se olvida, y meses después el sistema
    abre navegadores porque un día dijiste que sí.
    """
    p = sesion_web.conceder_permiso("iniciar sesión en Claude", duracion_s=0.05)
    assert p.vigente is True
    assert sesion_web.permiso_vigente() is not None

    time.sleep(0.1)
    assert p.vigente is False
    assert sesion_web.permiso_vigente() is None


def test_el_permiso_se_puede_revocar_en_el_acto():
    sesion_web.conceder_permiso("prueba")
    assert sesion_web.permiso_vigente() is not None
    sesion_web.revocar_permiso()
    assert sesion_web.permiso_vigente() is None


def test_el_permiso_lleva_su_motivo():
    """«Permiso concedido» sin más no dice para qué. Va a la auditoría."""
    p = sesion_web.conceder_permiso("iniciar sesión en Claude")
    assert p.motivo == "iniciar sesión en Claude"


def test_con_permiso_pero_sin_motor_sigue_sin_poder_abrirse(monkeypatch):
    """
    Las dos condiciones se comprueban por separado. Fiarse de una sola dejaría
    pasar una apertura que no puede funcionar, y el fallo aparecería como un
    cuelgue en vez de como un mensaje.
    """
    sesion_web.conceder_permiso("prueba")
    # ANTES: `if not hay_motor:` alrededor de las dos aserciones. En una
    # máquina con Camoufox descargado —la de desarrollo— la rama no entraba y
    # este test no comprobaba NADA, en silencio, pareciendo verde. Una
    # aserción condicionada al entorno es media aserción en cada mitad de las
    # máquinas donde corre.
    monkeypatch.setattr(sesion_web, "disponible",
                        lambda: (False, "Camoufox no está instalado"))

    puede, motivo = sesion_web.puede_abrir()
    assert puede is False
    assert "Camoufox" in motivo


# ------------------------------------------------- 3. nunca tu perfil

def test_el_perfil_es_de_magi_y_no_el_tuyo(datos_propios):
    """
    Leer el perfil de Chrome del usuario daría acceso a todas sus sesiones
    abiertas —correo, banco, todo—. Es exactamente el secuestro que
    `no_browser` vino a cerrar, y no se reabre.
    """
    perfil = sesion_web.perfil_dir()
    assert datos_propios in perfil.parents
    for prohibido in ("Google", "Chrome", "AppData\\Local\\Google", "Mozilla"):
        assert prohibido not in str(perfil)


# ------------------------------------------------- 4. las credenciales

def test_las_cookies_caducan(datos_propios, monkeypatch):
    """Una cookie de sesión es una credencial, no un fichero de configuración."""
    sesion_web.guardar_cookies("Claude", [{"name": "s", "value": "x"}])
    assert sesion_web.cookies_de("Claude") is not None

    monkeypatch.setattr(sesion_web, "CADUCIDAD_COOKIES_S", -1)
    assert sesion_web.cookies_de("Claude") is None


def test_las_cookies_se_pueden_borrar(datos_propios):
    """Una credencial que no se puede retirar es una fuga."""
    sesion_web.guardar_cookies("Claude", [{"name": "s", "value": "x"}])
    assert sesion_web.olvidar_cookies("Claude") is True
    assert sesion_web.cookies_de("Claude") is None


def test_sin_cookies_devuelve_None_y_no_una_lista_vacia(datos_propios):
    """
    `None` y `[]` son afirmaciones distintas: «no hay sesión» y «hay sesión sin
    cookies». La segunda haría que se intentara usar una sesión inexistente.
    """
    assert sesion_web.cookies_de("Claude") is None
    sesion_web.guardar_cookies("Claude", [])
    assert sesion_web.cookies_de("Claude") is None


def test_un_nombre_de_proveedor_raro_no_escapa_del_directorio(datos_propios):
    """El nombre llega desde un catálogo editable: no se usa tal cual."""
    sesion_web.guardar_cookies("../../fuera", [{"a": 1}])
    assert not (datos_propios.parent / "fuera.json").exists()


# ------------------------------------------------- lo que ve el panel

def test_el_estado_dice_que_falta_y_por_que(datos_propios, monkeypatch):
    """
    `EstadoSesion` es el registro que consume el panel, campo a campo: cada uno
    es una afirmación que se le va a enseñar al usuario.
    """
    # Mismo caso que arriba: el `if e.motor is None:` que había aquí no se
    # cumplía en la máquina de desarrollo, así que la afirmación importante
    # —que un «no disponible» venga siempre con su motivo— no se comprobaba.
    monkeypatch.setattr(sesion_web, "disponible",
                        lambda: (False, "el navegador no se ha descargado"))

    e = sesion_web.estado()
    assert isinstance(e, sesion_web.EstadoSesion)
    assert isinstance(e.proveedores_pendientes, list)
    # Claude ya NO es «pendiente»: exige tu cuenta, y aquí no se inicia sesión
    # en ningún sitio. «Pendiente» prometía que algún día se resolvería, y esa
    # promesa costó medio módulo construido para desbloquear un proveedor que
    # estaba disponible por otra puerta. Ahora el panel dice «cerrado» y por qué.
    assert "Claude" not in e.proveedores_pendientes
    assert "Claude" in e.proveedores_imposibles
    assert "cuenta" in e.proveedores_imposibles["Claude"]
    assert e.permiso_vigente is False and e.caduca_en_s == 0.0
    assert e.perfil, "el panel tiene que poder decir dónde vive el perfil"
    assert e.motor is None
    assert e.motivo_no_disponible, (
        "decir «no disponible» sin el motivo no permite arreglarlo")


def test_el_estado_refleja_el_permiso_y_las_cookies(datos_propios, monkeypatch):
    """Que el panel no muestre un estado congelado del arranque."""
    monkeypatch.setattr(sesion_web, "disponible", lambda: (True, "simulado"))
    sesion_web.guardar_cookies("Claude", [{"name": "s", "value": "x"}])
    sesion_web.conceder_permiso("iniciar sesión en Claude")

    e = sesion_web.estado()
    assert e.permiso_vigente is True and e.caduca_en_s > 0
    assert "Claude" in e.proveedores_con_cookies
    assert "Claude" not in e.proveedores_pendientes


def test_los_proveedores_que_la_necesitan_estan_nombrados_con_su_motivo():
    """
    Seis proveedores, cada uno con lo que le falta. Sin esto, el panel tendría
    que adivinar por qué un proveedor está fuera.
    """
    assert set(sesion_web.PROVEEDORES_QUE_LA_NECESITAN) == {
        "Claude", "OpenaiChat", "Copilot", "LMArena", "Cloudflare", "DeepInfra"}
    for prov, motivo in sesion_web.PROVEEDORES_QUE_LA_NECESITAN.items():
        assert motivo, f"{prov} sin motivo declarado"


def test_las_autorizaciones_se_registran_aparte_de_las_violaciones():
    """
    Una violación es algo que el sistema intentó a tus espaldas; una
    autorización es algo que tú pediste. Mezclarlas dejaría el registro sin
    poder distinguir un secuestro de un permiso.
    """
    assert hasattr(no_browser, "autorizadas")
    assert isinstance(no_browser.autorizadas(), list)


# ------------------------------------------- lo que el panel NO debe prometer

def test_el_panel_no_dice_pendiente_de_lo_que_es_imposible(monkeypatch):
    """
    «Pendiente» es una promesa. Estos seis no la pueden cumplir.

    LO QUE ESTO EVITA, Y YA PASÓ UNA VEZ
    ====================================
    El panel mostraba `Claude` como pendiente junto a los que solo necesitan
    una sesión anónima. De ahí salió la conclusión de que faltaba cosechar
    cookies, y de ahí medio este módulo —812 líneas— para desbloquear un
    proveedor que estaba disponible por otra puerta (Perplexity) sin ninguna
    cookie y sin ninguna cuenta.

    Un rótulo optimista no es amable: es caro.
    """
    monkeypatch.setattr(sesion_web, "disponible", lambda: (True, "simulado"))
    e = sesion_web.estado()

    for prov, motivo in sesion_web.IMPOSIBLES_POR_DISENO.items():
        assert prov not in e.proveedores_pendientes, (
            f"{prov} sale como «pendiente» y no lo está: {motivo}")
        assert prov in e.proveedores_imposibles
        assert e.proveedores_imposibles[prov], "cerrado sin motivo no ayuda"


def test_cada_imposible_dice_CUAL_de_los_dos_motivos_es():
    """
    No es lo mismo «necesita tu cuenta» que «abre un navegador». El primero
    depende de una regla tuya que podrías cambiar; el segundo, de §I.3, que
    define el proyecto. Mezclarlos impide decidir.
    """
    for prov, motivo in sesion_web.IMPOSIBLES_POR_DISENO.items():
        assert ("cuenta" in motivo) or ("navegador" in motivo), (
            f"{prov}: el motivo no dice de cuál de los dos casos se trata")


def test_no_se_promete_como_pendiente_nada_sin_via():
    """
    Los seis que necesitan sesión están hoy todos en la lista de imposibles.
    Si algún día uno deja de estarlo, este test lo dice — y entonces sí habrá
    algo pendiente de verdad, con su motivo.
    """
    assert set(sesion_web.IMPOSIBLES_POR_DISENO) == set(
        sesion_web.PROVEEDORES_QUE_LA_NECESITAN)
