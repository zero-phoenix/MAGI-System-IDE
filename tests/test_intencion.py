

def test_un_encargo_largo_que_menciona_mejora_no_es_aprobacion():
    """El caso medido el 2-sep-2026: «optimiza ... propon una mejora por
    cada filosofía...» se tragó como respuesta a una tarea zombi pendiente
    de aprobación y el encargo jamás arrancó."""
    from magi.modules.swarm.intencion import es_respuesta_a_aprobacion
    assert not es_respuesta_a_aprobacion(
        "optimiza el rendimiento del emulador y propon una mejora por cada "
        "una de las tres filosofias ortogonales")
    # Y lo que sí es revisión sigue siéndolo: verbo al mando, frase corta.
    assert es_respuesta_a_aprobacion("mejora el titulo a azul")
    assert es_respuesta_a_aprobacion("cambia el color del boton")
