import re


def _slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _build_series(name_prefix, short_description, description, base_price, stock, attributes, tags, image_prefix, variants):
    products = []
    for offset, variant in enumerate(variants):
        name = f"{name_prefix} {variant['label']}"
        products.append(
            {
                "name": name,
                "slug": _slugify(name),
                "short_description": short_description,
                "description": f"{description} {variant['description']}",
                "base_price": f"{base_price + variant['price_offset']:.2f}",
                "stock": stock + variant["stock_offset"],
                "attributes": {**attributes, **variant["attributes"]},
                "tags": tags + variant["tags"],
                "image_urls": [f"https://example.com/images/{image_prefix}-{offset + 1}.jpg"],
            }
        )
    return products


PRODUCT_SEED = []

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="MacBook Pro 14",
        short_description="Laptop premium cho dev, design va cong viec chuyen nghiep.",
        description="Dong laptop man hinh 14 inch, hieu nang manh, phu hop code, thiet ke va xu ly multimedia.",
        base_price=1899.00,
        stock=6,
        attributes={"category": "laptop", "brand": "Apple"},
        tags=["laptop", "premium", "developer"],
        image_prefix="macbook-pro-14",
        variants=[
            {"label": "M3 16GB 512GB", "price_offset": 0, "stock_offset": 2, "attributes": {"cpu": "M3", "ram": "16GB", "storage": "512GB"}, "tags": ["apple", "workstation"], "description": "Ban can bang cho nhu cau code va lam viec sang tao."},
            {"label": "M3 Pro 18GB 512GB", "price_offset": 250, "stock_offset": 1, "attributes": {"cpu": "M3 Pro", "ram": "18GB", "storage": "512GB"}, "tags": ["apple", "studio"], "description": "Tang suc manh cho IDE, docker va data workflow."},
            {"label": "M3 Pro 18GB 1TB", "price_offset": 450, "stock_offset": 0, "attributes": {"cpu": "M3 Pro", "ram": "18GB", "storage": "1TB"}, "tags": ["apple", "ssd"], "description": "Dung luong lon cho project, media va VM."},
            {"label": "M3 Max 36GB 1TB", "price_offset": 1100, "stock_offset": -1, "attributes": {"cpu": "M3 Max", "ram": "36GB", "storage": "1TB"}, "tags": ["apple", "creative"], "description": "Ban hieu nang cao cho render, AI local va video."},
            {"label": "M3 Max 36GB 2TB", "price_offset": 1600, "stock_offset": -2, "attributes": {"cpu": "M3 Max", "ram": "36GB", "storage": "2TB"}, "tags": ["apple", "pro"], "description": "Tap trung vao workload nang va storage du phong."},
            {"label": "M3 24GB 1TB", "price_offset": 600, "stock_offset": 0, "attributes": {"cpu": "M3", "ram": "24GB", "storage": "1TB"}, "tags": ["apple", "hybrid"], "description": "Lua chon can doi giua hieu nang va chi phi."},
        ],
    )
)

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="Dell XPS 13",
        short_description="Ultrabook gon nhe cho hoc tap, van phong va di chuyen.",
        description="Dong ultrabook mong nhe, man hinh dep, phu hop meeting, hoc tap va cong viec hang ngay.",
        base_price=1299.00,
        stock=8,
        attributes={"category": "laptop", "brand": "Dell"},
        tags=["laptop", "ultrabook", "office"],
        image_prefix="dell-xps-13",
        variants=[
            {"label": "FHD i5 8GB 512GB", "price_offset": 0, "stock_offset": 3, "attributes": {"cpu": "Intel Core i5", "ram": "8GB", "storage": "512GB", "display": "FHD"}, "tags": ["dell", "daily"], "description": "Hop voi nhu cau hoc tap va van phong co ban."},
            {"label": "FHD i7 16GB 512GB", "price_offset": 180, "stock_offset": 2, "attributes": {"cpu": "Intel Core i7", "ram": "16GB", "storage": "512GB", "display": "FHD"}, "tags": ["dell", "business"], "description": "Tang RAM va CPU cho multitasking tot hon."},
            {"label": "OLED i7 16GB 1TB", "price_offset": 420, "stock_offset": 1, "attributes": {"cpu": "Intel Core i7", "ram": "16GB", "storage": "1TB", "display": "OLED"}, "tags": ["dell", "premium"], "description": "Man hinh tot cho visual va lam viec di dong."},
            {"label": "OLED Ultra 7 16GB 1TB", "price_offset": 520, "stock_offset": 0, "attributes": {"cpu": "Intel Core Ultra 7", "ram": "16GB", "storage": "1TB", "display": "OLED"}, "tags": ["dell", "ai-pc"], "description": "Phu hop workflow moi va pin tot hon."},
            {"label": "Ultra 7 32GB 1TB", "price_offset": 700, "stock_offset": -1, "attributes": {"cpu": "Intel Core Ultra 7", "ram": "32GB", "storage": "1TB", "display": "FHD+"}, "tags": ["dell", "power-user"], "description": "Danh cho nguoi can nhieu RAM va cong viec nang vua."},
            {"label": "Developer Edition 16GB 512GB", "price_offset": 210, "stock_offset": 1, "attributes": {"cpu": "Intel Core i7", "ram": "16GB", "storage": "512GB", "os": "Ubuntu"}, "tags": ["dell", "linux"], "description": "Phien ban hop voi dev muon dung Linux san."},
        ],
    )
)

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="Logitech G Pro X",
        short_description="Phu kien gaming tap trung vao chat voice va esports.",
        description="Dong phu kien cho game thu can do tre thap, do ben va kha nang set up nhanh.",
        base_price=79.00,
        stock=15,
        attributes={"category": "gaming-accessory", "brand": "Logitech"},
        tags=["gaming", "logitech", "accessory"],
        image_prefix="logitech-g-pro-x",
        variants=[
            {"label": "Headset Wired", "price_offset": 50, "stock_offset": 4, "attributes": {"type": "headset", "connection": "3.5mm"}, "tags": ["audio", "esports"], "description": "Tap trung chat voice ro va de deo lau."},
            {"label": "Headset Wireless", "price_offset": 110, "stock_offset": 2, "attributes": {"type": "headset", "connection": "wireless"}, "tags": ["audio", "wireless"], "description": "Giai phong day noi choi game va hop voice."},
            {"label": "Superlight Mouse", "price_offset": 70, "stock_offset": 5, "attributes": {"type": "mouse", "weight": "63g"}, "tags": ["mouse", "fps"], "description": "Toi uu cho tracking nhanh va flick shot."},
            {"label": "Mechanical Keyboard", "price_offset": 40, "stock_offset": 3, "attributes": {"type": "keyboard", "switch": "GX Brown"}, "tags": ["keyboard", "tkl"], "description": "Ban phim TKL cho game thu can compact setup."},
            {"label": "Mousepad XL", "price_offset": -20, "stock_offset": 8, "attributes": {"type": "mousepad", "size": "XL"}, "tags": ["deskmat", "setup"], "description": "Bo sung be mat cho chuot chuyen dong on dinh."},
            {"label": "Streaming Microphone", "price_offset": 30, "stock_offset": 1, "attributes": {"type": "microphone", "pickup": "cardioid"}, "tags": ["streaming", "creator"], "description": "Phu hop stream va call voi am thanh sach."},
        ],
    )
)

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="Samsung Odyssey",
        short_description="Man hinh cho gaming, streaming va workstation setup.",
        description="Dong monitor toc do cao, kich thuoc rong, phu hop setup choi game va lam viec da cua so.",
        base_price=279.00,
        stock=10,
        attributes={"category": "monitor", "brand": "Samsung"},
        tags=["monitor", "display", "desk-setup"],
        image_prefix="samsung-odyssey",
        variants=[
            {"label": "G4 25 inch 240Hz", "price_offset": 0, "stock_offset": 4, "attributes": {"refresh_rate": "240Hz", "size": "25 inch"}, "tags": ["gaming", "fhd"], "description": "Tap trung cho esports va toc do phan hoi cao."},
            {"label": "G5 27 inch 165Hz", "price_offset": 90, "stock_offset": 3, "attributes": {"refresh_rate": "165Hz", "size": "27 inch", "resolution": "QHD"}, "tags": ["gaming", "qhd"], "description": "Can bang giua hinh anh net va gia thanh."},
            {"label": "G6 32 inch 240Hz", "price_offset": 220, "stock_offset": 1, "attributes": {"refresh_rate": "240Hz", "size": "32 inch", "resolution": "QHD"}, "tags": ["gaming", "curve"], "description": "Hop voi game AAA va goc nhin rong."},
            {"label": "OLED G8 34 inch", "price_offset": 620, "stock_offset": 0, "attributes": {"panel": "OLED", "size": "34 inch", "resolution": "UWQHD"}, "tags": ["oled", "ultrawide"], "description": "Phien ban cho creator va streamer muon mau sac dep."},
            {"label": "Neo G7 43 inch", "price_offset": 540, "stock_offset": -1, "attributes": {"panel": "Mini LED", "size": "43 inch", "resolution": "4K"}, "tags": ["4k", "console"], "description": "Lua chon cho ban lam viec lon hoac console setup."},
            {"label": "G9 49 inch", "price_offset": 940, "stock_offset": -2, "attributes": {"size": "49 inch", "resolution": "DQHD", "panel": "VA"}, "tags": ["super-ultrawide", "multitask"], "description": "Tap trung workflow da cua so va dashboard."},
        ],
    )
)

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="Nike Dri-FIT",
        short_description="Trang phuc tap luyen thoang khi, de van dong moi ngay.",
        description="Dong do tap co chat lieu hut am, nhanh kho, phu hop gym, chay bo va lifestyle nang dong.",
        base_price=25.00,
        stock=20,
        attributes={"category": "clothes", "brand": "Nike"},
        tags=["clothes", "training", "sportswear"],
        image_prefix="nike-dri-fit",
        variants=[
            {"label": "Training Shirt Black", "price_offset": 0, "stock_offset": 5, "attributes": {"type": "shirt", "color": "black", "fit": "regular"}, "tags": ["nike", "shirt"], "description": "Mau trung tinh de mac hang ngay va tap luyen."},
            {"label": "Training Shirt White", "price_offset": 0, "stock_offset": 4, "attributes": {"type": "shirt", "color": "white", "fit": "regular"}, "tags": ["nike", "shirt"], "description": "Phien ban sang mau cho phong cach toi gian."},
            {"label": "Running Tee Blue", "price_offset": 8, "stock_offset": 3, "attributes": {"type": "shirt", "color": "blue", "fit": "slim"}, "tags": ["nike", "running"], "description": "Tap trung cho chay bo va hoat dong cardio."},
            {"label": "Training Shorts Gray", "price_offset": 5, "stock_offset": 6, "attributes": {"type": "shorts", "color": "gray", "fit": "regular"}, "tags": ["nike", "shorts"], "description": "Quan ngan nhe, de tap gym va di bo."},
            {"label": "Jogger Pants Black", "price_offset": 18, "stock_offset": 2, "attributes": {"type": "pants", "color": "black", "fit": "tapered"}, "tags": ["nike", "jogger"], "description": "Hop voi phong cach active hang ngay."},
            {"label": "Zip Hoodie Navy", "price_offset": 30, "stock_offset": 1, "attributes": {"type": "hoodie", "color": "navy", "fit": "regular"}, "tags": ["nike", "outerwear"], "description": "Them lop ao khoac nhe cho thoi tiet mat."},
        ],
    )
)

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="Uniqlo Smart Casual",
        short_description="Trang phuc co ban de di hoc, di lam va mac hang ngay.",
        description="Dong trang phuc basic de mix do, tap trung vao tinh tien dung, form de mac va gia hop ly.",
        base_price=19.00,
        stock=18,
        attributes={"category": "clothes", "brand": "Uniqlo"},
        tags=["clothes", "casual", "daily-wear"],
        image_prefix="uniqlo-smart-casual",
        variants=[
            {"label": "Oxford Shirt White", "price_offset": 10, "stock_offset": 4, "attributes": {"type": "shirt", "color": "white", "material": "cotton"}, "tags": ["uniqlo", "oxford"], "description": "Mau co ban cho smart casual va office."},
            {"label": "Oxford Shirt Blue", "price_offset": 10, "stock_offset": 4, "attributes": {"type": "shirt", "color": "blue", "material": "cotton"}, "tags": ["uniqlo", "oxford"], "description": "Ban xanh nhat de phoi voi quan toi mau."},
            {"label": "Airism Polo Gray", "price_offset": 14, "stock_offset": 3, "attributes": {"type": "polo", "color": "gray", "material": "airism"}, "tags": ["uniqlo", "polo"], "description": "Thoang khi cho mua nong va di chuyen."},
            {"label": "Chino Pants Beige", "price_offset": 18, "stock_offset": 2, "attributes": {"type": "pants", "color": "beige", "fit": "slim"}, "tags": ["uniqlo", "chino"], "description": "Quan de mix voi ao so mi va tee."},
            {"label": "U Crew Neck Tee Black", "price_offset": 0, "stock_offset": 5, "attributes": {"type": "tee", "color": "black", "material": "cotton"}, "tags": ["uniqlo", "tee"], "description": "Item basic de layer va mac hang ngay."},
            {"label": "Light Down Vest Olive", "price_offset": 35, "stock_offset": 1, "attributes": {"type": "vest", "color": "olive", "material": "down"}, "tags": ["uniqlo", "outerwear"], "description": "Ao khoac nhe de di chuyen va layer."},
        ],
    )
)

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="Sony WH-1000XM",
        short_description="Tai nghe chong on cho hoc tap, di chuyen va lam viec tap trung.",
        description="Dong headphone va earbud khong day cho am thanh on dinh, chong on tot va pin dai.",
        base_price=149.00,
        stock=12,
        attributes={"category": "audio", "brand": "Sony"},
        tags=["audio", "wireless", "travel"],
        image_prefix="sony-wh-1000xm",
        variants=[
            {"label": "XM4 Black", "price_offset": 0, "stock_offset": 3, "attributes": {"type": "headphone", "color": "black"}, "tags": ["sony", "anc"], "description": "Phien ban can doi giua gia va tinh nang."},
            {"label": "XM4 Silver", "price_offset": 0, "stock_offset": 2, "attributes": {"type": "headphone", "color": "silver"}, "tags": ["sony", "anc"], "description": "Lua chon mau sang cho office setup."},
            {"label": "XM5 Black", "price_offset": 120, "stock_offset": 1, "attributes": {"type": "headphone", "color": "black"}, "tags": ["sony", "flagship"], "description": "Nang cap ve chat am va call clarity."},
            {"label": "XM5 Blue", "price_offset": 130, "stock_offset": 0, "attributes": {"type": "headphone", "color": "blue"}, "tags": ["sony", "flagship"], "description": "Mau sac noi bat cho nguoi di chuyen."},
            {"label": "WF Earbuds Black", "price_offset": -20, "stock_offset": 4, "attributes": {"type": "earbuds", "color": "black"}, "tags": ["sony", "compact"], "description": "Dang nho gon, hop voi gym va di lai."},
            {"label": "WF Earbuds White", "price_offset": -20, "stock_offset": 2, "attributes": {"type": "earbuds", "color": "white"}, "tags": ["sony", "compact"], "description": "Phien ban trang cho phong cach toi gian."},
        ],
    )
)

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="Anker Power Bundle",
        short_description="Phu kien sac va ket noi cho laptop, phone va travel kit.",
        description="Dong phu kien Anker tap trung vao tinh co dong, sac nhanh va su dung on dinh trong cong viec hang ngay.",
        base_price=19.00,
        stock=25,
        attributes={"category": "accessory", "brand": "Anker"},
        tags=["accessory", "charging", "travel"],
        image_prefix="anker-power-bundle",
        variants=[
            {"label": "USB-C Cable 1m", "price_offset": 0, "stock_offset": 8, "attributes": {"type": "cable", "length": "1m"}, "tags": ["anker", "usb-c"], "description": "Cap co ban cho sac nhanh va dong bo."},
            {"label": "USB-C Cable 2m", "price_offset": 4, "stock_offset": 7, "attributes": {"type": "cable", "length": "2m"}, "tags": ["anker", "usb-c"], "description": "Cap dai hon cho ban lam viec va phong ngu."},
            {"label": "Nano Charger 30W", "price_offset": 16, "stock_offset": 5, "attributes": {"type": "charger", "power": "30W"}, "tags": ["anker", "charger"], "description": "Cu sac nho gon cho dien thoai va tablet."},
            {"label": "Nano Charger 65W", "price_offset": 32, "stock_offset": 4, "attributes": {"type": "charger", "power": "65W"}, "tags": ["anker", "charger"], "description": "Sac duoc laptop mỏng nhe va phu kien."},
            {"label": "Power Bank 10000", "price_offset": 28, "stock_offset": 6, "attributes": {"type": "power-bank", "capacity": "10000mAh"}, "tags": ["anker", "portable"], "description": "Du dung cho chuyen di ngan va backup."},
            {"label": "USB-C Hub 7 in 1", "price_offset": 45, "stock_offset": 3, "attributes": {"type": "hub", "ports": "7 in 1"}, "tags": ["anker", "desk-setup"], "description": "Mo rong cong ket noi cho laptop."},
        ],
    )
)

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="Adidas Daily Move",
        short_description="Giay va do mac theo phong cach active everyday.",
        description="Dong san pham cho di bo, tap luyen nhe va outfit nang dong hang ngay.",
        base_price=42.00,
        stock=16,
        attributes={"category": "footwear", "brand": "Adidas"},
        tags=["footwear", "sportswear", "daily"],
        image_prefix="adidas-daily-move",
        variants=[
            {"label": "Running Shoes White", "price_offset": 28, "stock_offset": 4, "attributes": {"type": "shoes", "color": "white"}, "tags": ["adidas", "running"], "description": "Giay nhe de chay bo va di lai hang ngay."},
            {"label": "Running Shoes Black", "price_offset": 28, "stock_offset": 4, "attributes": {"type": "shoes", "color": "black"}, "tags": ["adidas", "running"], "description": "Ban mau toi de giu sach va de phoi."},
            {"label": "Court Sneakers White", "price_offset": 18, "stock_offset": 3, "attributes": {"type": "sneakers", "color": "white"}, "tags": ["adidas", "streetwear"], "description": "Phu hop outfit casual va di hoc."},
            {"label": "Slides Navy", "price_offset": -8, "stock_offset": 5, "attributes": {"type": "slides", "color": "navy"}, "tags": ["adidas", "summer"], "description": "De dep di lai nhanh sau tap luyen."},
            {"label": "Training Duffel Bag", "price_offset": 5, "stock_offset": 2, "attributes": {"type": "bag", "color": "black"}, "tags": ["adidas", "gym"], "description": "Tui dung do gym gon, de sap xep."},
            {"label": "Baseball Cap Black", "price_offset": -12, "stock_offset": 6, "attributes": {"type": "cap", "color": "black"}, "tags": ["adidas", "outdoor"], "description": "Phu kien nhe cho di chuyen va tap ngoai troi."},
        ],
    )
)

PRODUCT_SEED.extend(
    _build_series(
        name_prefix="Kindle Reading Kit",
        short_description="Thiet bi va phu kien cho doc sach, hoc tap va ghi chu.",
        description="Dong thiet bi doc sach va phu kien xoay quanh viec hoc tap, tap trung va tieu thu noi dung dai.",
        base_price=89.00,
        stock=9,
        attributes={"category": "reading", "brand": "Amazon"},
        tags=["reading", "study", "focus"],
        image_prefix="kindle-reading-kit",
        variants=[
            {"label": "Kindle Basic 16GB", "price_offset": 0, "stock_offset": 3, "attributes": {"type": "ereader", "storage": "16GB"}, "tags": ["kindle", "ebook"], "description": "May doc sach co ban cho nguoi moi bat dau."},
            {"label": "Kindle Paperwhite 16GB", "price_offset": 50, "stock_offset": 2, "attributes": {"type": "ereader", "storage": "16GB"}, "tags": ["kindle", "waterproof"], "description": "Nang cap man hinh va den doc de chiu hon."},
            {"label": "Kindle Paperwhite 32GB", "price_offset": 85, "stock_offset": 1, "attributes": {"type": "ereader", "storage": "32GB"}, "tags": ["kindle", "audiobooks"], "description": "Hop voi nguoi tai nhieu sach va audiobook."},
            {"label": "Fabric Cover Black", "price_offset": -55, "stock_offset": 4, "attributes": {"type": "cover", "color": "black"}, "tags": ["kindle", "case"], "description": "Bao ve may doc sach khi di lai."},
            {"label": "Fabric Cover Blue", "price_offset": -55, "stock_offset": 3, "attributes": {"type": "cover", "color": "blue"}, "tags": ["kindle", "case"], "description": "Mau sac nhe cho setup hoc tap."},
            {"label": "Reading Stand", "price_offset": -35, "stock_offset": 2, "attributes": {"type": "stand", "material": "aluminum"}, "tags": ["desk-setup", "study"], "description": "Gia do nho gon de doc ban tay roi."},
        ],
    )
)
