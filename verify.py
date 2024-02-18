import pypdf
import glob

def extract(x, indent=-1):
    res = ""
    if isinstance(x, list):
        for y in x:
            res += extract(y, indent+1)
    else:
        res += "  " * indent + x['/Title'].strip() + "\n"
    return res


def main():
    for x in glob.glob("data/*.pdf"):
        reader = pypdf.PdfReader(x)
        toc = extract(reader.outline)
        file = x[:-4] + ".txt"
        with open(file, 'w') as fp:
            fp.write(toc)

if __name__ == "__main__":
    main()
