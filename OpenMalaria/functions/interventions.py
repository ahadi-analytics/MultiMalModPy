import os


# Currently SMC is not supported


def carrying_capacity(exp, xml):
    snippet_file = "intervention_CCstep.txt"
    with open(
        os.path.join(exp.openmalaria_input_path, "snippets", snippet_file),
        "r",
        encoding="utf-8",
    ) as file:
        snippet = file.read()
    xml = xml.replace("@intervention_ccstep@", snippet)
    return xml
