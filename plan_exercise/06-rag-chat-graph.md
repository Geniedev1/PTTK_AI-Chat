# Plan 06: RAG va Chat dua tren KB_Graph

## Muc tieu

Lam ro va nang cap phan chat de co the noi "chat dua tren KB_Graph", khong chi la chat chung.

## Kien truc de xuat

Context cho chat nen den tu 3 nguon:

1. Product/policy chunks
2. Graph context
3. Realtime API cho gia, ton kho, order

De nop bai, phai chi ro graph context tham gia vao retrieval/generation the nao.

## Viec phai lam

1. Chot graph-first retrieval rule:
   - lay user interest tu graph
   - lay product neighbors tu graph
   - lay query path tu graph
2. Tang logging cho `used_graph_context`.
3. Them response fields debug:
   - `graph_context`
   - `sources`
   - `retrieval_mode`
4. Viet 5-10 cau hoi demo:
   - hoi san pham lien quan
   - hoi goi y theo so thich
   - hoi policy
   - hoi gia/ton kho runtime
5. Viet file test scenario chat.
6. Neu can, uu tien graph context truoc lexical retrieval trong mot so intent recommendation/advice.

## Output bat buoc

- chat flow co graph context xuat hien ro
- test/demo prompts
- debug response ghi duoc graph source

## Definition of Done

- Co it nhat 1 nhom cau hoi ma answer thay doi khi co graph context.
- Co the trinh bay ro "graph dung o dau trong RAG pipeline".
- Realtime intents van route sang API that.

## Evidence can nop

- 3 transcript chat co source.
- JSON response co `used_graph_context=true`.
- So do retrieval flow.
