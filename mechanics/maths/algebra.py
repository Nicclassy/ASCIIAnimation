import math
import operator
import re
from fractions import Fraction
from typing import Optional, Literal, Iterator, Any

from typing_extensions import Self

from mechanics.constants import (
    INTEGER_PATTERN, REPLACE_EXPONENT_SIGN, ADD_MULTIPLICATION_OPERATOR,
    FUNCTION_SUBSTITUTIONS, ADD_PARAMETER_PATTERN
)
from mechanics.movement.position import RelativePosition
from mechanics.types import Numeric

OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '^': pow,
}


def degrees_to_radians(degrees: Numeric) -> Numeric:
    return degrees / 180 * math.pi


def format_coefficient_magnitude(coefficient: Numeric, degree: int) -> Optional[Literal[""] | Numeric]:
    coefficient_magnitude = abs(coefficient)
    if not degree or coefficient_magnitude != 1:
        return coefficient if Term.allow_negative_coefficients else coefficient_magnitude
    elif coefficient_magnitude == 1:
        return '-' if Term.allow_negative_coefficients and coefficient < 0 else ''
    return None


def format_float_coefficient(coefficient: Numeric | str) -> Numeric | str:
    if type(coefficient) is float:
        return int(coefficient) if int(coefficient) == coefficient else coefficient
    elif type(coefficient) is str or type(coefficient) is int:
        return coefficient


def format_string_decimal_coefficient(coefficient: Numeric) -> str:
    coefficient = format_float_coefficient(coefficient)
    if type(coefficient) is float:
        return f"({str(Fraction(coefficient).limit_denominator())})"
    else:
        return str(coefficient)


class Term:

    r"""
    A pythonic implementation of algebraic representations of constant and variable quantities defined in mathematics.
    Originally designed only to cater for integers, the class is now compatible for floating point quantities
    as coefficients (but not as exponents).
    The regular expression defining a term is stated below:

    | ^-?\d+(\\.\\d+)?\w?(\\^\\d)?$

    Terms are pythonically constructed in two parts: a coefficient and a degree; the fundamental constitutents
    of an algebraic term.
    The string form of this class is an Infix notation representation of the term.
    There are two ways in which a term can be constructed:

    | 1. via Reverse Polish Notation (a classmethod is used for this)
    | 2. identifying the components of a term by identifying its coefficient and exponent

    The pronumeral is by default 't' and should not be changed.
    """

    PRONUMERAL = "t"
    allow_negative_coefficients = True

    def __init__(self, coefficient: Numeric = 1, degree: int = 0):
        self._coefficient = (int if INTEGER_PATTERN.match(str(coefficient)) else float)(coefficient)
        self._degree = 0 if not self._coefficient else degree

    def __bool__(self) -> bool:
        return not (self._degree == 0 and self._coefficient == 0)

    def __neg__(self) -> Self:
        self._coefficient = -self._coefficient
        return self

    def __add__(self, other: Self) -> Self:
        return Term(self._coefficient + other.coefficient, self._degree)

    def __sub__(self, other: Self) -> Self:
        return self + -other

    def __mul__(self, other: Self) -> Self:
        return Term(self._coefficient * other.coefficient, self._degree + other.degree)

    def __truediv__(self, other: Self) -> Self:
        return Term(format_float_coefficient(self._coefficient / other.coefficient), self._degree)

    def __pow__(self, exponent: int) -> Self:
        return Term(self._coefficient ** exponent, self._degree * exponent) if exponent != 0 else Term(1)

    def __str__(self) -> str:
        coefficient = format_coefficient_magnitude(self._coefficient, self._degree)
        coefficient = format_string_decimal_coefficient(coefficient)
        return '{}{}{}{}'.format(coefficient,
                                 Term.PRONUMERAL if self._degree > 0 else '',
                                 '^' if self._degree > 1 else '',
                                 self._degree if self._degree > 1 else '')

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    @property
    def coefficient(self) -> Numeric:
        return self._coefficient

    @property
    def degree(self) -> int:
        return self._degree

    def is_negative(self) -> bool:
        return self._coefficient < 0

    def is_constant(self) -> bool:
        return self._degree == 0

    def integrate_power_rule(self, integrations: int = 1):
        for _ in range(integrations):
            self._coefficient = format_float_coefficient(self._coefficient / (self._degree + 1))
            self._degree += 1


ADD_PARAMETER = re.compile(ADD_PARAMETER_PATTERN.format(Term.PRONUMERAL))


class VariableConstantTerm(Term):

    """
    A pythonic implementation of a term which also stores algebraic pronumeral constants (multiplicative).
    Examples in this project include:

    | -at^2
    | bt
    | Vtsin(θ)
    | Vtcos(θ)

    where each term is with respect to the pronumeral of the term class.
    """

    def __init__(self, variable_constants: list, coefficient: Numeric = 1, degree: int = 0):
        super().__init__(coefficient, degree)
        self._variable_constants = variable_constants

    def __str__(self) -> str:
        coefficient = format_coefficient_magnitude(self._coefficient, self._degree)
        coefficient = format_string_decimal_coefficient(coefficient)
        if coefficient.isdigit() and int(coefficient) == 1:
            coefficient = ""
        return '{}{}{}{}{}'.format(coefficient, "".join(self._variable_constants),
                                   Term.PRONUMERAL if self._degree > 0 else '',
                                   '^' if self._degree > 1 else '',
                                   self._degree if self._degree > 1 else '')

    @property
    def variable_constants(self) -> list[str]:
        return self._variable_constants

    def integrate_power_rule(self, integrations: int = 1):
        self._coefficient = format_float_coefficient(self._coefficient / (self._degree + 1))
        self._degree += 1


class Expression:

    """
    Stores a heterogeneous sequence of terms, including variable constant terms.
    Evaluations may be performed through the insertion of operands via regular expression substitutions,
    which involves replacing empty strings.
    """

    def __init__(self, *terms: Any):
        self._terms = list(terms)

    def __iter__(self) -> Iterator:
        return iter(self._terms)

    def __getitem__(self, index: int) -> Term:
        return self._terms[index]

    def __len__(self) -> int:
        return len(self._terms)

    def __neg__(self) -> Self:
        return Expression(*[-item for item in self])

    def __bool__(self) -> bool:
        return bool(self._terms)

    def __add__(self, other: Self) -> Self:
        return Expression(*(self._terms + other.terms))

    def __sub__(self, other: Self) -> Self:
        return self + -other

    def __mul__(self, other: Self) -> Self:
        return Expression(*[term * other_term for term in self._terms for other_term in other.terms])

    def __pow__(self, other: Self) -> Self:
        expression = Expression(Term())
        exponent = other[0].coefficient
        for _ in range(exponent if exponent else 0):
            expression *= self
        return expression

    def __str__(self) -> str:
        Term.allow_negative_coefficients = False
        expression_result = ''
        for index, term in enumerate(sorted(self._terms, key=operator.attrgetter("degree"), reverse=True)):
            if not term.coefficient:
                continue
            if term.is_negative():
                if index == 0:
                    expression_result += '-' + str(term)
                else:
                    expression_result += ' - ' + str(term)
            else:
                if index == 0:
                    expression_result += str(term)
                else:
                    expression_result += ' + ' + str(term)
        Term.allow_negative_coefficients = True
        return expression_result or '0'

    def __repr__(self) -> str:
        return f'Expression({self})'

    @property
    def terms(self) -> list[Term]:
        return self._terms

    def simplify(self):
        expression_terms = []
        previous_power = -1
        for term in sorted(self._terms, key=operator.attrgetter("degree"), reverse=True):
            power = term.degree
            if power == previous_power:
                previous_term = expression_terms.pop(-1)
                expression_terms.append(term + previous_term)
            else:
                expression_terms.append(term)
            previous_power = power
        self._terms = expression_terms

    def evaluate(self, substitutions: dict) -> Numeric:
        string_to_evaluate = ""
        for term_no, term in enumerate(self._terms, 1):
            if type(term) is VariableConstantTerm:
                terms = term.variable_constants.copy()
                if term.degree >= 1:
                    terms.append(str(Term(degree=term.degree, coefficient=term.coefficient)))
                    string_to_evaluate += " * ".join(terms)
                else:
                    string_to_evaluate += " + " + " + ".join(terms)
            else:
                string_to_evaluate += str(term) + (" + " if term_no < len(self._terms) else "")
        string_to_evaluate = REPLACE_EXPONENT_SIGN.sub(" ** ", string_to_evaluate)
        string_to_evaluate = ADD_MULTIPLICATION_OPERATOR.sub(" * ", string_to_evaluate)
        return eval(string_to_evaluate, FUNCTION_SUBSTITUTIONS | substitutions)

    @classmethod
    def from_rpn(cls, rpn_stack: list) -> Self:
        formatted_stack = []
        while rpn_stack:
            term = rpn_stack.pop(0)
            if term.isdigit():
                formatted_stack.append(cls(Term(coefficient=term)))
            elif term == Term.PRONUMERAL:
                formatted_stack.append(cls(Term(degree=1)))
            elif term in OPERATORS:
                last_term = formatted_stack.pop()
                second_last_term = formatted_stack.pop()
                formatted_stack.append(OPERATORS[term](second_last_term, last_term))
        expression = formatted_stack[0]
        expression.simplify()
        return expression

    def integrate_power_rule(self, constant_of_integration: Optional[VariableConstantTerm | Term] = None):
        for term in self._terms:
            if term:
                term.integrate_power_rule()
        if constant_of_integration is not None and constant_of_integration:
            self._terms.append(constant_of_integration)


class ParametricEquation(Expression):

    """
    An expression represented in parametric form.
    """

    def __init__(self, x_parameter: Optional[Expression] = None, *terms: Any):
        super().__init__(*terms)
        self._x_parameter = x_parameter or Expression(Term(degree=1))

    def evaluate(self, substitutions: dict) -> Numeric:
        string_to_evaluate = ""
        for term_no, term in enumerate(self._terms, 1):
            if type(term) is VariableConstantTerm:
                terms = term.variable_constants.copy()
                add_plus = False
                if term_no > 1:
                    previous_term = self._terms[term_no - 2]
                    if previous_term.degree != term.degree:
                        add_plus = True
                if term.degree >= 1:
                    # Prevent squaring/exponentiating the negative operand; -5 ** 2 is 25, but we don't want that
                    terms.extend([str(Term(degree=term.degree)), str(Term(coefficient=term.coefficient))])
                    if add_plus:
                        string_to_evaluate += " + "
                    string_to_evaluate += " * ".join(terms)
                else:
                    string_to_evaluate += " + " + " + ".join(terms)
            else:
                string_to_evaluate += str(term) + (" + " if term_no < len(self._terms) else "")
        # To understand how this works, add a print(string_to_evaluate) after each of the following lines
        string_to_evaluate = ADD_PARAMETER.sub(f"({Term.PRONUMERAL})", string_to_evaluate)
        string_to_evaluate = REPLACE_EXPONENT_SIGN.sub(" ** ", string_to_evaluate)
        string_to_evaluate = ADD_MULTIPLICATION_OPERATOR.sub(" * ", string_to_evaluate)
        return eval(string_to_evaluate, FUNCTION_SUBSTITUTIONS | substitutions)

    def get_position_at_time(self, time: float, substitutions: Optional[dict] = None) -> RelativePosition:
        x = self._x_parameter.evaluate({"t": time})
        y = self.evaluate({"t": time} | (substitutions or {}))
        return RelativePosition(int(y), int(x))


class ExponentialEquation:

    def __init__(self, limit: Numeric):
        self._limit = limit

    def get_value_at_time(self, time: float) -> Numeric:
        exponent = round(math.log(self._limit) - time, 2)
        return self._limit - round(math.e, 2) ** exponent
