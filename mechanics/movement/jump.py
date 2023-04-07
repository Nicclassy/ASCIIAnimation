from typing import Literal

from mechanics.types import Numeric
from mechanics.movement.vectors import Vector
from mechanics.maths.algebra import Term, VariableConstantTerm, Expression, ParametricEquation


class JumpMovement:
    """
    Initialises a parametric equation in the form

    | x = t
    | y = -at^2 + bt

    to model the height increase as a result of jumping.

    Consider that such an equation only accounts for the change in position rather than
    a new position in its entirety.

    To derive the equations below,
    where H is the max height of the equation,
    and T is the time of flight of the equation,

    | a = (4H) / (T ^ 2)
    | b = (4H) / T

    The deriving of the two equations is listed below:

    | When y = 0, t = T
    | t(b - aT) = 0
    | b = aT
    | T = b / a

    The value of H occurs at the axis of symmetry (variable a is negative)

    | x = -b / (-2a) = b / (2a)

    Hence,

    | H = y(b / 2a)
    | H = (-ab^2) / (4a^2) + b(b / 2a)
    | H = (b ^ 2) / (2a) + (b ^ 2) / (2a)
    | H = (2b - b^2) / (4a)
    | H = (b ^ 2) / (4a)

    Simultaneously equating these equations we get:

    | T = b / a           ---> (1)
    | H = (b ^ 2) / (4a)  ---> (2)

    Rearranging (1), we get:

    | a = b / T

    Substituting this into (2), we get:

    | H = (bT) / 4
    | 4H = bt
    | b = (4H) / T

    Substituting this back into (1), we get:

    | a = ((4H) / T) / T
    | a = (4H) / (T ^ 2)

    Hence, as aforementioned:

    | a = (4H) / (T ^ 2)
    | b = (4H) / T

    In the constructor, max_height represents H and time_of_flight represents T
    """

    def __init__(self, max_height: Numeric, time_of_flight: Numeric,
                 projection_quadrant: Literal[1, 2, 3, 4]):
        self.__a = 4 * max_height / time_of_flight ** 2
        self.__b = 4 * max_height / time_of_flight
        self.__projection_quadrant = projection_quadrant
        self.__parametric_equation = ParametricEquation(Expression(Term(coefficient=0)),
                                                        VariableConstantTerm(["a"], coefficient=-1, degree=2),
                                                        VariableConstantTerm(["b"], degree=1))

    def get_vector_at_time(self, time: float, terrain_height: int, terrain_width: int) -> Vector:
        substitutions = {"a": self.__a, "b": self.__b}
        relative_position = self.__parametric_equation.get_position_at_time(time, substitutions)
        position_y = relative_position.normalize(self.__projection_quadrant, terrain_height, terrain_width)[0]
        # Position is to be added from INITIAL jump pos; consider LR movement as well
        return Vector(position_y)


if __name__ == "__main__":
    j = JumpMovement(6, 6, 2)
    for i in range(12):
        print(j.get_vector_at_time(i, 12, 12)[::-1])
