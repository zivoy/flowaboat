from io import BytesIO

import discord
import regex
import sympy
from PIL import Image, ImageOps
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations, implicit_multiplication_application)

from utils.discord import DiscordInteractive, help_me
from utils.utils import PickeledServerDict, Log

interact = DiscordInteractive.interact

mathUsers = PickeledServerDict("./config/usermath.pickle")
mathUsers.load()

commands = ["solve", "parse", "p","latex", "parselatex", "expand", "simplify", "sub", "get", "getlatex","show","approx", "n"]


class Command:
    command = "math"
    description = "do math with the sympy library\n" \
                  "commands:\n" \
                  "\t- solve\n" \
                  "\t- parse\n" \
                  "\t- latex\n" \
                  "\t- parseLatex\n" \
                  "\t- expand\n" \
                  "\t- simplify\n" \
                  "\t- sub\n" \
                  "\t- show\n" \
                  "\t- approx\n" \
                  "\t- derive"
    argsRequired = 1
    usage = "<command> [arguments]"
    examples = [{
        'run': "math parse x=12y",
        'result': "an image of x=12y and the ability to use in future commands"
    }]
    synonyms = ["sympy", "m"]

    async def call(self, package):
        message, args = package["message_obj"], package["args"]
        DiscordInteractive.client = package["client"]

        if message.guild.id not in mathUsers.dictionary:
            mathUsers.dictionary[message.guild.id] = dict()

        if len(args) < 2 or not args[1].lower() in commands:
            Log.error("No command provided")
            await help_me(message, self.command)
            return

        math_text = "".join(args[2:])
        math_text = regex.sub(r"\n?```\n?", "", math_text).replace("`", "")
        ans = False
        if message.author.id in mathUsers.dictionary[message.guild.id] and \
                (r"\ans" in math_text or ":ans:" in math_text):
            ans = mathUsers.dictionary[message.guild.id][message.author.id]

        math: sympy.Expr = None

        notneeded = [r"\left", r"\right", r"\big", r"\Big", r"\bigg", r"\Bigg", r"\middle", r"\,", r"\:", r"\;"]
        if args[1].lower() in ["parse", "get", "p"]:
            if len(args) < 3:
                Log.error("No math provided")
                interact(message.channel.send, "Please provide a math equation sympy allowed")
                return
            if ans:
                for i in notneeded:
                    ans = ans.replace(i, "")
                ans = str(parse_latex_equation(ans))
                math_text = math_text.replace(r"\ans", ans).replace(":ans:", ans)
            math = parse_string_equation(math_text)
            mathUsers.dictionary[message.guild.id][message.author.id] = sympy.latex(math)

        if args[1].lower() in ["parselatex", "getlatex"]:
            if len(args) < 3:
                Log.error("No math provided")
                interact(message.channel.send, "Please provide a latex equation")
                return
            if ans:
                ans = f" {ans} "
                math_text = math_text.replace(r"\ans", ans).replace(":ans:", ans)
            for i in notneeded:
                math_text = math_text.replace(i, "")
            math = parse_latex_equation(math_text)
            # math = replace_exp(math)
            mathUsers.dictionary[message.guild.id][message.author.id] = sympy.latex(math)

        if math is None and message.author.id in mathUsers.dictionary[message.guild.id]:
            math = parse_latex_equation(mathUsers.dictionary[message.guild.id][message.author.id])
        elif math is not None:
            pass
        else:
            Log.error("No math provided")
            interact(message.channel.send, "You have no math, parse something first")
            return

        Log.log(math)

        if args[1].lower() in ["latex"]:
            interact(message.channel.send, f"```\n{sympy.latex(math)}\n```")
            return

        if args[1].lower() == "solve":
            if len(args) < 3:
                Log.error("No variable provided")
                interact(message.channel.send, "Please provide a variable to solve for")
                return
            symbol = sympy.symbols(args[2])
            if symbol not in math.free_symbols:
                Log.error("Invalid Variable")
                interact(message.channel.send, "Please provide a valid variable")
                return
            solutions = sympy.solve(math, symbol)
            if len(solutions) == 1:
                math = sympy.Eq(symbol, solutions[0])
            else:
                eqs = [sympy.Eq(symbol, i) for i in solutions]
                math = sympy.Matrix(eqs)
            mathUsers.dictionary[message.guild.id][message.author.id] = sympy.latex(math)

        if args[1].lower() == "expand":
            math = sympy.expand(math)
            mathUsers.dictionary[message.guild.id][message.author.id] = sympy.latex(math)

        if args[1].lower() == "simplify":
            math = sympy.simplify(math)
            mathUsers.dictionary[message.guild.id][message.author.id] = sympy.latex(math)

        if args[1].lower() == "sub":
            if len(args) < 3:
                Log.error("No variable(s) provided")
                interact(message.channel.send, "Please provide a variable to solve for")
                return
            subs = dict()
            for i in regex.finditer(r"([A-z]+) ?= ?([^ ,]+)", math_text):
                variable = parse_string_equation(i.group(1))
                value = parse_string_equation(i.group(2))
                if variable not in math.free_symbols:
                    Log.error("Invalid Variable")
                    interact(message.channel.send, f"Please provide a valid variable, not {variable}")
                    return
                subs[variable] = value

            math = math.subs(list(subs.items()))
            mathUsers.dictionary[message.guild.id][message.author.id] = sympy.latex(math)

        if args[1].lower() in ["approx", "n"]:
            math = sympy.N(math)
            mathUsers.dictionary[message.guild.id][message.author.id] = sympy.latex(math)
            interact(message.channel.send, f"```\n{variable}\n```")
            return

        mathUsers.save()
        image = render_latex(math)
        byteImgIO = BytesIO()
        image.save(byteImgIO, "PNG")
        byteImgIO.seek(0)
        math_image = discord.File(byteImgIO, "mathimage.png")
        image.close()
        byteImgIO.close()
        interact(message.channel.send, file=math_image)
        return


def render_latex(text, euler=False, dpi=200, border=3):
    if not isinstance(text, str):
        text = sympy.latex(text)
    text = f"$${text}$$"
    obj = BytesIO()
    sympy.preview(text, output='png', viewer='BytesIO', outputbuffer=obj, euler=euler,
                  dvioptions=["-T", "tight", "-z", "0", "--truecolor", f"-D {dpi}"])
    img = ImageOps.expand(Image.open(obj), border=border, fill=(255, 255, 255))
    obj.close()

    return img


def parse_latex_equation(string):
    if "=" in string:
        return sympy.Eq(*map(parse_latex_equation, string.split("=", 1)))
    return parse_latex(string)


def parse_string_equation(string):
    eq = r"\equalssign"
    string = string.replace("^", "**")
    string = string.replace("=<", f"{eq}<").replace("=>", f"{eq}>").replace("<=", f"<{eq}").replace(">=", f">{eq}")
    if "=" in string:
        string = string.replace(eq, "=")
        return sympy.Eq(*map(parse_string_equation, string.split("=", 1)))
    string = string.replace(eq, "=")
    string = catch_exp(string)
    return parse_expr(string, transformations=(standard_transformations + (implicit_multiplication_application,)))


brackets = {"{": "}", "(": ")"}


def run_brackets(string, bracket, index):
    close = brackets[bracket]
    while index < len(string):
        curr = string[index]
        if curr in brackets:
            index = run_brackets(string, curr, index + 1)
            continue
        if curr == close:
            return index
        index += 1


def catch_exp(string):
    pos = 0
    newstring = ""
    for i in regex.finditer(r"e\*\*(-?[^\+\-\*\/])", string):
        idx = i.span()
        newstring += string[pos:idx[0]]
        if string[idx[0] + 3] == "(":
            endpos = run_brackets(string, "(", idx[0] + 3)
            newstring += "exp"
            newstring += string[idx[0] + 3:endpos]
            pos = endpos
        else:
            newstring += "exp("
            newstring += i.group(1)
            newstring += ")"
            pos = idx[1]
    newstring += string[pos:len(string)]
    return newstring


def replace_exp(expr):
    newstring = catch_exp(str(expr))
    if newstring == str(expr):
        return expr
    return parse_expr(newstring)
