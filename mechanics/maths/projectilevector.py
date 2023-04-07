from typing import Optional

from typing_extensions import Self

from mechanics.movement.vectors import Vector
from mechanics.movement.position import Position, RelativePosition
from mechanics.maths.algebra import Numeric, Term, VariableConstantTerm, Expression, degrees_to_radians


class ProjectileVector:

    g = "g"
    a = "θ"
    V = "V"
    t = Term.PRONUMERAL
    h = "h"
    d = "d"
    assert t == "t"

    def __init__(self, y: Expression, x: Expression):
        self._j_component = y
        self._i_component = x

    def __repr__(self) -> str:
        return f"ProjectileVector({self})"

    def __str__(self) -> str:
        output = ""
        if self._i_component:
            i_component = str(self._i_component)
            if len(self._i_component) > 1:
                output += "(" + i_component + ")"
            else:
                output += i_component
            output += "i"
        if self._j_component:
            j_component = str(self._j_component)
            if len(output) > 0:
                output += " + "
            if len(self._j_component) > 1:
                output += "(" + j_component + ")"
            else:
                output += j_component
            output += "j"
        return output

    def integrate(self, i_component_constant: Optional[VariableConstantTerm | Term] = None,
                  j_component_constant: Optional[VariableConstantTerm | Term] = None,
                  inplace: bool = False) -> Self:
        if inplace:
            projectile_vector = self
        else:
            projectile_vector = ProjectileVector(self._j_component, self._i_component)
        projectile_vector._i_component.integrate_power_rule(i_component_constant)
        projectile_vector._j_component.integrate_power_rule(j_component_constant)
        if not inplace:
            return projectile_vector

    def get_position_at_values(self, velocity: Numeric, angle: Numeric,
                               time: Numeric,
                               starting_position: Optional[RelativePosition] = None,
                               return_float: bool = False) -> RelativePosition:
        # Where angle is in degrees
        starting_position = starting_position or Position.ORIGIN
        substitutions = {
            ProjectileVector.a: degrees_to_radians(angle),
            ProjectileVector.V: velocity,
            ProjectileVector.t: time,
            ProjectileVector.h: starting_position[0],
            ProjectileVector.d: starting_position[1],
        }
        x_value = self._i_component.evaluate(substitutions)
        y_value = self._j_component.evaluate(substitutions)
        # For projectile vector:
        # return ProjectileVector(y=Expression(Term(coefficient=y_value)), x=Expression(Term(coefficient=x_value)))
        if return_float:
            return RelativePosition(y_value, x_value)
        else:
            return RelativePosition(int(y_value), int(x_value))


def derive_equations_of_motion(x_acceleration: Expression, y_acceleration: Expression,
                               velocity_x_constant: VariableConstantTerm,
                               velocity_y_constant: VariableConstantTerm,
                               displacement_x_constant: Term,
                               displacement_y_constant: Term) -> ProjectileVector:
    acceleration_vector = ProjectileVector(y_acceleration, x_acceleration)
    velocity_vector = acceleration_vector.integrate(velocity_x_constant, velocity_y_constant)
    return velocity_vector.integrate(displacement_x_constant, displacement_y_constant)


def get_displacement_vector(gravity: Numeric = 0,
                            displacement_y_constant: Optional[Numeric] = None,
                            displacement_x_constant: Optional[Numeric] = None) -> ProjectileVector:
    if displacement_x_constant is None:
        displacement_x_constant = VariableConstantTerm(["d"])
    else:
        displacement_x_constant = Term(coefficient=displacement_x_constant)

    if displacement_y_constant is None:
        displacement_y_constant = VariableConstantTerm(["h"])
    else:
        displacement_y_constant = Term(coefficient=displacement_y_constant)

    return derive_equations_of_motion(x_acceleration=Expression(),
                                      y_acceleration=Expression(Term(-gravity or -10)),
                                      velocity_x_constant=VariableConstantTerm(["V", f"cos({ProjectileVector.a})"]),
                                      velocity_y_constant=VariableConstantTerm(["V", f"sin({ProjectileVector.a})"]),
                                      displacement_x_constant=displacement_x_constant,
                                      displacement_y_constant=displacement_y_constant
                                      )


if __name__ == "__main__":
    displacement_vector = get_displacement_vector()
    print(displacement_vector)
    v = displacement_vector.get_position_at_values(velocity=22, angle=60, time=2,
                                                   starting_position=RelativePosition(5, 5))
    print(Vector(*v))
