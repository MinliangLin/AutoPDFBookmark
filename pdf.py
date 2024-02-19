import re
from collections import Counter
from dataclasses import dataclass

import fire
import pypdf


@dataclass(frozen=True)
class Data:
    page_num: int
    font_size: float
    text: str
    left: float
    top: float
    font: str


data = []
page_num = 0


def visitor(text, cm, tm, font_dict, font_size):
    ctm = pypdf.mult(cm, tm)
    font = font_dict.get("/BaseFont", "") if isinstance(font_dict, dict) else ""
    data.append(
        Data(
            page_num=page_num,
            font_size=font_size,
            text=text,
            left=ctm[-2],
            top=ctm[-1] + font_size,
            font=font,
        )
    )


def index_of_abstract(lst):
    for i, x in enumerate(lst):
        if x.text.lower().strip() == "abstract":
            return i
    return -1


def guess(x: Data, most: float):
    if x.font_size > most:
        return True
    # TODO: it seems that '/Subtype': '/Type0' in font should be used?
    if x.font_size == most and x.font.lower().endswith("-medi"):
        # return True
        p = re.compile(r"[\div\.]+\s.*", re.IGNORECASE)
        if p.match(x.text) is not None:
            return True
        # NOTE: the abstract hack here is ugly hack here.
        if  x.text.lower().strip() == "abstract":
            return True
    return False


def validate(x):
    # NOTE: remove arxiv side notation
    if x.text.lower().startswith("arxiv:"):
        return False
    if len(x.text.strip()) > 0 and \
        x.top >= 0 and x.left >= 0:
        return True
    return False


def main(inp, out, force=False):
    reader = pypdf.PdfReader(inp)
    writer = pypdf.PdfWriter(out)

    if reader.outline and not force:
        return f"{inp} already has outline!!"

    for page in reader.pages:
        writer.add_page(page)
        page.extract_text(visitor_text=visitor)
        global page_num
        page_num += 1

    global data
    data = [x for x in data if validate(x)]

    metadata = reader.metadata
    writer.add_metadata(metadata)

    most = Counter([x.font_size for x in data]).most_common(1)[0][0]
    sections = [x for x in data if guess(x, most)]

    if (idx := index_of_abstract(sections)) >= 0:
        sections = sections[idx + 1 :]

    stack = []
    for x in sections:
        fit = pypdf.generic.Fit.xyz(left=x.left, top=x.top)

        # Pop elements from the stack that are of a lower or equal level
        while stack and stack[-1][0].font_size <= x.font_size:
            stack.pop()
        
        if stack:
            # If there's an element in the stack, it is the parent
            parent = stack[-1][1]
            obj = writer.add_outline_item(title=x.text, page_number=x.page_num, fit=fit, parent=parent)
        else:
            # If stack is empty, there's no parent
            obj = writer.add_outline_item(title=x.text, page_number=x.page_num, fit=fit)
        
        # Push the current element onto the stack
        stack.append((x, obj))

    with open(out, "wb") as fp:
        writer.write(fp)


if __name__ == "__main__":
    fire.Fire(main)
