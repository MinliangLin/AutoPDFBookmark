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
        if x.text.lower() == "abstract":
            return i
    return -1


def guess(x, most):
    if x.font_size > most.font_size:
        return True
    if x.font_size == most.font_size and x.font.lower().endswith("-medi"):
        # return True
        p = re.compile(r"[\div\.]+\s.*", re.IGNORECASE)
        if p.match(x.text) is not None:
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
    data = [x for x in data if len(x.text.strip()) > 0]

    metadata = reader.metadata
    writer.add_metadata(metadata)

    cnt = Counter(data)
    most = max(data, key=lambda x: cnt.get(x))
    large = [x for x in cnt if guess(x, most)]

    if (idx := index_of_abstract(large)) >= 0:
        large = large[idx + 1 :]

    prev = None
    for x in large:
        fit = pypdf.generic.Fit.xyz(left=x.left, top=x.top)
        if prev is not None and prev[0].font_size > x.font_size:
            writer.add_outline_item(
                title=x.text, page_number=x.page_num, fit=fit, parent=prev[1]
            )
        else:
            obj = writer.add_outline_item(title=x.text, page_number=x.page_num, fit=fit)
            prev = (x, obj)

    with open(out, "wb") as fp:
        writer.write(fp)


if __name__ == "__main__":
    fire.Fire(main)
