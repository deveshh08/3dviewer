"""
Maps iPromo product categories (from URL or breadcrumb) to GLB filenames.
Returns None if no matching GLB exists (triggers flat photo fallback).
"""

CATEGORY_TO_GLB = [
    (["quarter-zip", "quarter_zip", "1/4 zip"], "quarter_zip.glb"),
    (["crew-neck", "crewneck", "crew neck"],     "crewneck.glb"),
    (["hoodie", "hooded"],                       "hoodie.glb"),
    (["sweatshirt", "sweatpant", "jogger"],      "crewneck.glb"),
    (["t-shirt", "tshirt", "tank top", "tee"],  "tshirt.glb"),
    (["performance shirt", "long sleeve"],       "tshirt.glb"),
    (["polo", "golf shirt"],                     "polo.glb"),
    (["lightweight jacket", "soft shell", "windbreaker"], "lightweight_jacket.glb"),
    (["fleece", "vest"],                         "fleece_vest.glb"),
    (["puffer", "insulated", "parka"],           "lightweight_jacket.glb"),
    (["baseball cap", "trucker hat", "snapback", "fitted cap"], "baseball_cap.glb"),
    (["beanie", "knit hat", "winter hat"],       "beanie.glb"),
    (["bucket hat", "visor"],                    "baseball_cap.glb"),
    (["tote", "shopping bag"],                   "tote_bag.glb"),
    (["backpack", "drawstring"],                 "backpack.glb"),
    (["tumbler", "travel mug", "water bottle", "coffee mug"], "tumbler.glb"),
]


# Only GLB files that actually exist in frontend/public/models/
AVAILABLE_GLBS = {"quarter_zip.glb"}


def get_glb_for_category(url: str, breadcrumbs: list) -> str | None:
    search_text = (url + " " + " ".join(breadcrumbs)).lower()
    for keywords, glb_file in CATEGORY_TO_GLB:
        if any(kw in search_text for kw in keywords):
            return glb_file if glb_file in AVAILABLE_GLBS else None
    return None


if __name__ == "__main__":
    tests = [
        ("https://www.ipromo.com/crosswind-quarter-zip-sweatshirt.html",
         ["Apparel", "Sweatshirts & Sweatpants", "Quarter-Zips"],
         "quarter_zip.glb"),
        ("https://www.ipromo.com/apparel/t-shirts/short-sleeve-t-shirts/gildan.html",
         ["Apparel", "T-Shirts", "Short Sleeve T-Shirts"],
         "tshirt.glb"),
        ("https://www.ipromo.com/food-candy/gourmet/chocolate.html",
         ["Food & Candy", "Gourmet", "Chocolate"],
         None),
    ]
    for url, crumbs, expected in tests:
        result = get_glb_for_category(url, crumbs)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url.split('/')[-1]} → {result} (expected {expected})")
