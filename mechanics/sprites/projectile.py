from typing import Optional, Literal

from mechanics.constants import (
    FUNCTION_SUBSTITUTIONS, REPLACE_EXPONENT_SIGN, ADD_MULTIPLICATION_OPERATOR, HORIZONTAL_RANGE_FORMULA,
    MAX_HEIGHT_FORMULA,
)
from mechanics.types import CharacterList2D
from mechanics.maths.algebra import ParametricEquation, Expression, Term
from mechanics.movement.position import Position, RelativePosition
from mechanics.sprites.mixins import MovableSpriteMixin, TimedPositionMovementMixin, PositionMovementMixin
from mechanics.maths.projectilevector import Numeric, get_displacement_vector, ProjectileVector, degrees_to_radians


class ProjectileSprite(MovableSpriteMixin, PositionMovementMixin, TimedPositionMovementMixin):
    """
    Quadrant definitions
    Quadrant 1: y values are the same, x values are measured from the right side
    Quadrant 2: No change
    Quadrant 3: y values measured from the top, x values are the same
    Quadrant 4: Both x and y values are measured from the opposite sides
    """

    def __init__(self, data: CharacterList2D | str, projection_quadrant: Literal[1, 2, 3, 4],
                 starting_position: Position):
        super().__init__(data, starting_position)
        TimedPositionMovementMixin.__init__(self)
        self._starting_position = starting_position
        self._projection_quadrant = projection_quadrant

    def get_position_at_time(self, time: Numeric, terrain_height: int, terrain_width: int) -> Position:
        pass


class StandardProjectileSprite(ProjectileSprite):

    def __init__(self, data: CharacterList2D | str, velocity: Numeric, angle: Numeric,
                 gravity: Numeric, projection_quadrant: Literal[1, 2, 3, 4],
                 starting_position: Position):
        super().__init__(data, projection_quadrant, starting_position)
        self._vector = get_displacement_vector(gravity)
        self._gravity = gravity
        self._angle = angle
        self._velocity = velocity

    def __repr__(self) -> str:
        return f"{self.__class__}(velocity={self._velocity}, angle={self._angle}, gravity={self._gravity}," \
               f"vector={self._vector})"

    def get_position_at_time(self, time: Numeric, terrain_height: int, terrain_width: int) -> Position:
        time -= self._start_time
        relative_position = self._vector.get_position_at_values(self._velocity, self._angle, time)
        relative_position += self._starting_position
        position = relative_position.normalize(self._projection_quadrant, terrain_height, terrain_width)
        return position

    def evaluate_formula_at_values(self, formula: tuple[str, str]) -> RelativePosition:
        starting_position = self._starting_position or Position.ORIGIN
        substitutions = {
            ProjectileVector.g: self._gravity,
            ProjectileVector.a: degrees_to_radians(self._angle),
            ProjectileVector.V: self._velocity,
            ProjectileVector.h: starting_position[0],
            ProjectileVector.d: starting_position[1],
        }
        formula_y, formula_x = formula
        formula_y = REPLACE_EXPONENT_SIGN.sub(" ** ", formula_y)
        formula_y = ADD_MULTIPLICATION_OPERATOR.sub(" * ", formula_y)
        formula_x = REPLACE_EXPONENT_SIGN.sub(" ** ", formula_x)
        formula_x = ADD_MULTIPLICATION_OPERATOR.sub(" * ", formula_x)
        y_value = eval(formula_y, substitutions | FUNCTION_SUBSTITUTIONS)
        x_value = eval(formula_x, substitutions | FUNCTION_SUBSTITUTIONS)
        return RelativePosition(int(y_value), int(x_value))

    def get_max_height(self) -> Numeric:
        return self.evaluate_formula_at_values(MAX_HEIGHT_FORMULA)

    def get_horizontal_range(self) -> Numeric:
        return self.evaluate_formula_at_values(HORIZONTAL_RANGE_FORMULA)


class EquationProjectileSprite(ProjectileSprite):

    """
    Class which stores equations, whether they be linear or parabolic
    """

    def __init__(self, data: CharacterList2D | str, projection_quadrant: Literal[1, 2, 3, 4],
                 parametric_equation: ParametricEquation,
                 starting_position: Optional[Position]):
        super().__init__(data, projection_quadrant, starting_position)
        self._starting_position = starting_position
        self._parametric_equation = parametric_equation

    def get_position_at_time(self, time: Numeric, terrain_height: int, terrain_width: int) -> Position:
        time -= self._start_time
        relative_position = self._parametric_equation.get_position_at_time(time)
        position = relative_position.normalize(self._projection_quadrant, terrain_height, terrain_width)
        return position + self._starting_position


class LinearEquationSprite(EquationProjectileSprite):

    def __init__(self, data: CharacterList2D | str, projection_quadrant: Literal[1, 2, 3, 4],
                 gradient: Numeric, starting_position: Position):
        parametric_equation = ParametricEquation(Expression(Term(degree=1)), Term(degree=1, coefficient=gradient))
        super().__init__(data, projection_quadrant, parametric_equation, starting_position)


class StraightLineEquationSprite(EquationProjectileSprite):

    def __init__(self, data: CharacterList2D | str, projection_quadrant: Literal[1, 2],
                 gradient: Numeric, starting_position: Position):
        parametric_equation = ParametricEquation(Expression(Term(coefficient=gradient, degree=1)), Term(coefficient=0))
        super().__init__(data, projection_quadrant, parametric_equation, starting_position)
