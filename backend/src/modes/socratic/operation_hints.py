"""Hint levels 0 to 2 for one operation on two whole numbers (23 + 45, 7 × 8).

0 restates the goal with the child's numbers, 1 names the concept and 2 isolates
a smaller step: the units, counting on, one row less of the table. Level 3, the
worked example, is in hints.py.
"""

__all__ = ["LADDERS"]


def _suma(a: int, b: int, level: int) -> str:
    if level == 0:
        return (
            f"¡Vamos a pensarlo juntos! Queremos juntar {a} y {b}. ¿Por dónde empiezas?"
        )
    if level == 1:
        return (
            f"Sumar es juntar. Si tienes {a} y te dan {b} más, ¿cuántos tienes? "
            "Puedes separar cada número en decenas y unidades."
        )
    if a < 10 and b < 10:
        return f"Empieza en {max(a, b)} y cuenta {min(a, b)} más. ¿A qué número llegas?"
    return f"Empieza por las unidades: ¿cuánto es {a % 10} + {b % 10}?"


def _resta(a: int, b: int, level: int) -> str:
    if level == 0:
        return f"Vamos a pensar en {a} - {b}. ¿Qué pasa cuando a {a} le quitas {b}?"
    if level == 1:
        return (
            f"Restar es quitar. Si tienes {a} y quitas {b}, ¿cuántos quedan? "
            f"También puedes pensar: ¿qué número sumado a {b} da {a}?"
        )
    if a < 10:
        return f"Empieza en {a} y cuenta hacia atrás {b}. ¿A qué número llegas?"
    if a - b < 10:  # the units step (32 - 25 → 12 - 5) would be the whole answer
        return f"Cuenta desde {b} hasta llegar a {a}. ¿Cuántos pasos das?"
    units_a, units_b = a % 10, b % 10
    if units_a >= units_b:
        return f"Empieza por las unidades: ¿cuánto es {units_a} - {units_b}?"
    return (
        f"Las unidades {units_a} son menos que {units_b}: pide prestada una "
        f"decena. ¿Cuánto es {units_a + 10} - {units_b}?"
    )


def _multiplicacion(a: int, b: int, level: int) -> str | None:
    if level == 0:
        return f"Vamos a pensar en {a} × {b}. ¿Qué significa multiplicar {a} por {b}?"
    if level == 1:
        return (
            f"Multiplicar es sumar el mismo número varias veces: {a} × {b} es "
            f"sumar {a}, {b} veces. ¿Cómo empezarías?"
        )
    if b < 2:
        return None
    return f"{a} × {b} es {a} × {b - 1} más otro {a}. ¿Cuánto es {a} × {b - 1}?"


def _division(a: int, b: int, level: int) -> str:
    if level == 0:
        return f"Vamos a pensar en {a} ÷ {b}. ¿Qué significa repartir {a} entre {b}?"
    if level == 1:
        return (
            f"Dividir es repartir en partes iguales. Si repartes {a} entre {b}, "
            f"¿cuántos le tocan a cada uno? Piensa en la tabla del {b}."
        )
    return (
        f"¿Qué número multiplicado por {b} da {a}? Prueba la tabla del {b}: "
        f"{b} × 1 = {b}, {b} × 2 = {b * 2}. ¿Sigues?"
    )


LADDERS = {
    "suma": _suma,
    "resta": _resta,
    "multiplicacion": _multiplicacion,
    "division": _division,
}
