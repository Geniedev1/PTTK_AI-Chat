# Plan 13: Defense Demo Readiness and Rubric Evidence Pack

## Trang thai

Planned.

## Muc tieu

Dong goi toan bo ket qua ky thuat thanh bo ho so bao ve de toi da diem theo rubric:

- Product service
- Deep model
- KB
- RAG + chat
- Tich hop ecom

Trong tam la trinh bay ro rang, demo on dinh, va co bang chung cho tung tieu chi cham.

## Dau vao va phu thuoc

Phu thuoc vao:

- Plan 01-10 (baseline)
- Plan 11 (deep model MVP)
- Plan 12 (evaluation report)

## Scope bat buoc

- tao rubric-evidence matrix (tieu chi -> bang chung -> file/chung minh)
- tao demo script end-to-end theo kich ban co thu tu
- tao checklist pre-demo va fallback plan
- tao bo slide/noi dung tom tat 10-15 phut
- chot danh sach cau hoi kho va cau tra loi ngan

## Khong lam trong plan nay

- khong doi kien truc lon vao phut cuoi
- khong them tinh nang moi ngoai rubric impact

## Rubric evidence map (bat buoc)

Moi tieu chi phai co:

- bang chung code
- bang chung test hoac metric
- bang chung demo runtime
- cau noi giai thich gia tri kinh doanh

## Demo scenarios de bao ve

### Scenario 1: Behavioral recommendation

- user/session co interaction history
- recommendation thay doi theo profile va deep score
- hien reason_codes + source_signals

### Scenario 2: Grounded chat va realtime routing

- hoi policy/product retrieval co source
- hoi order/cart/price/stock route realtime
- show used_realtime_api, retrieval_mode, source_ids

### Scenario 3: End-to-end ecom integration

- search -> click -> cart -> order -> interaction event
- refresh recommend/chat context sau event moi
- show su thay doi truoc/sau

## Artifacts can chot

- rubric-mapping document
- demo-runbook (command + expected output)
- FAQ bao ve (Q&A ngan)
- fallback runbook khi mat API key/LLM
- final summary report link den metric Plan 12

## Operational checklist truoc gio bao ve

- docker compose up on dinh
- data seed da nap
- API key va env da set
- endpoint smoke test pass
- backup path khi OpenAI unavailable da san sang

## Viec phai lam

1. Tao rubric-evidence matrix.
2. Viet runbook cho 3 demo scenarios.
3. Chot checklist pre-demo va fallback.
4. Tong hop key metrics tu Plan 12 vao slide.
5. Luyen tap demo theo timeline 10-15 phut.

## Deliverable

- rubric-evidence pack
- demo script + runbook
- fallback operational note
- concise defense summary
- Q&A cheat sheet

## Definition of Done

- moi tieu chi rubric deu co bang chung ro rang
- demo chay on dinh theo script, khong bi dut flow
- co fallback khi external AI gap su co
- co thong diep ket luan ngan gon ve gia tri he thong
- team co the trinh bay thong nhat va tra loi hoi dong tu tin

## Risk chinh

- demo phu thuoc internet/API key
- script demo qua dai, vuot thoi gian
- bang chung metric khong lien ket truc tiep toi rubric

## Thu tu thuc hien de tranh no scope

1. Rubric map
2. Demo runbook
3. Fallback checklist
4. Slide summary
5. Dry run 2-3 lan truoc bao ve
