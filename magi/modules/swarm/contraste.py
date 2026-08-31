"""
El contraste de la síntesis contra el registro (C12, P5).

Se mudó de `orchestrator.py` —donde nació— al quedarse su casa sin sitio:
el orquestador rozaba su techo de líneas y las fases 7 y 8 del megaplan
(abanico y réplica) tenían que cablearse justo ahí. La regla de los
trinquetes es clara: no se sube el techo en silencio, y adelgazar extrayendo
lógica cohesiva es la opción que la propia regla ofrece. Esto no es un
refactor decorativo: es el mismo código, con sus porqués, en su propio
módulo.

QUÉ HACE
========
Casper redacta la síntesis; este módulo la compara con lo que el registro
de la tarea dice que PASÓ DE VERDAD. Si la síntesis se atribuye un hecho
comprobable que el registro no sostiene, se devuelve un aviso que viaja con
la entrega. El contraste no es contra otro modelo —volveríamos a preguntar
a quien ya se equivocó— sino contra el registro de lo que el sistema HIZO.
"""
from __future__ import annotations

#: Verbos con los que una síntesis se atribuye un hecho comprobable. Se
#: comparan en minúsculas y sin acentos, y solo importan si el registro
#: dice que ese hecho no ocurrió.
_AFIRMACIONES = ("se compilo", "se compiló", "compilado exitosamente",
                 "se empaqueto", "se empaquetó", "se genero el ejecutable",
                 "se generó el ejecutable", "binario generado",
                 "ejecutable creado", "se creo el .exe", "se creó el .exe")


def con_el_registro(state: dict, verdict: dict) -> str | None:
    """
    ¿La síntesis se está atribuyendo algo que no pasó? (C12)

    LA PRUEBA QUE OBLIGÓ A ESCRIBIR ESTO
    ====================================
    20-ago, encargo «ping pong a color de 16 bits en un .exe portable».
    Casper cerró con:

        **Decisión Técnica:** APPROVED
        Empaquetado Portable Final (PyInstaller): Se compiló exitosamente
        el binario ejecutable único portable (onefile)…

    Cero bloques de código en toda la conversación, cero llamadas a la
    herramienta de entrega, cero artefactos. El informe parecía perfecto y
    el usuario se habría ido a buscar un fichero que no existe.

    Es peor que fallar: fallar se ve. Por eso el contraste no es contra
    otro modelo —volveríamos a preguntar a quien ya se equivocó— sino
    contra el registro de lo que el sistema HIZO.
    """
    texto = (verdict.get("feedback") or "")
    bajo = texto.lower()
    hubo_artefacto = bool(state.get("artefactos") or state.get("exe_path"))
    verificacion = state.get("verification") or {}

    if any(a in bajo for a in _AFIRMACIONES):
        if not (hubo_artefacto or verificacion.get("passed")):
            return ("[AVISO] La síntesis dice haber compilado o empaquetado "
                    "algo, y en el registro de esta tarea NO consta ningún "
                    "artefacto generado ni verificación en verde. Trátalo "
                    "como una propuesta, no como una entrega: no hay "
                    "fichero que buscar.")

    # P5 — EL CONTRASTE NO PUEDE CUBRIR SOLO «SE COMPILÓ».
    #
    # C12 nació de un caso concreto —una síntesis que decía haber
    # empaquetado un .exe inexistente— y se quedó ahí. Pero la forma del
    # fallo no tiene nada que ver con compilar: es **atribuirse un hecho
    # comprobable que el registro no sostiene**, y eso se puede decir de
    # muchas maneras.
    #
    # Es el principio que yo aplico sobre mi propio trabajo: desconfiar del
    # informe de éxito. Dos veces en la sesión del 20-ago me cazó a mí:
    # una prueba de alfa que fallaba porque mi expectativa estaba mal, y un
    # primer informe de Ritsuko cuyo veredicto era el mensaje de error del
    # proveedor — exactamente el fallo que Ritsuko existe para denunciar,
    # cometido por mí.
    #
    # Un sistema que solo se revisa en el caso que ya le pillaron aprende
    # a esquivar ese caso, no a ser honesto.
    for señales, sostiene, aviso in _AFIRMACIONES_EXTRA:
        if any(s in bajo for s in señales):
            if not sostiene(state, verificacion, hubo_artefacto):
                return aviso
    return None


#: (señales, ¿lo sostiene el registro?, qué se avisa si no).
#:
#: Cada entrada nombra una familia de afirmaciones que el sistema puede
#: comprobar sobre sí mismo. Si no se puede comprobar, NO se pone aquí:
#: avisar sobre lo que no se sabe es ruido, y el ruido enseña a ignorar
#: los avisos.
_AFIRMACIONES_EXTRA: tuple[tuple[tuple[str, ...], object, str], ...] = (
    (("las pruebas pasan", "los tests pasan", "tests en verde",
      "pruebas en verde", "se ejecutaron los tests",
      "se ejecutaron las pruebas", "suite en verde"),
     lambda st, ver, art: bool(ver.get("passed")),
     "[AVISO] La síntesis dice que las pruebas pasan, y en el registro de "
     "esta tarea NO consta ninguna verificación ejecutada en verde. Nadie "
     "ha corrido nada: es una previsión, no un resultado."),

    (("he escrito el fichero", "se escribio el fichero",
      "se escribió el fichero", "fichero creado", "archivo creado",
      "guardado en disco"),
     lambda st, ver, art: art or bool(st.get("ficheros_escritos")),
     "[AVISO] La síntesis dice haber escrito un fichero y en el registro "
     "no consta ninguno. Comprueba la ruta antes de darla por buena."),

    (("segun analyze_port", "según analyze_port", "el analizador indica",
      "la herramienta devuelve", "segun compare_consoles",
      "según compare_consoles"),
     lambda st, ver, art: bool(st.get("evidencia_previa")),
     "[AVISO] La síntesis cita el resultado de una herramienta que no se "
     "llegó a ejecutar en esta tarea. Es una cita de memoria, no un dato: "
     "trátala como tal."),
)
