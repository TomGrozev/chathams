import pymupdf

doc = pymupdf.open("/home/dev/workspace/test_scan.pdf")
page = doc[0]
print("pages", doc.page_count, "rect", page.rect)
print("text repr:", repr(page.get_text())[:400])
pix = page.get_pixmap(dpi=300, colorspace=pymupdf.csGRAY)
pix.save("/tmp/bench/work/page300.png")
print("raster", pix.width, pix.height)
