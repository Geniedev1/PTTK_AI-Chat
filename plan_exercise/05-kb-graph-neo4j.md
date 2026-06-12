# Plan 05: KB_Graph voi Neo4j

## Muc tieu

Bien data hanh vi thanh knowledge base graph co query duoc va demo duoc.

## Node/edge toi thieu

Node:

- `User`
- `Product`
- `Category`
- `Query`

Edge:

- `VIEWED`
- `CLICKED`
- `ADDED_TO_CART`
- `SEARCHED`
- `PURCHASED`

## Viec phai lam

1. Chot mapping `CSV action -> graph edge`.
2. Dam bao graph builder doc duoc file `data_user500.csv` hoac event full export.
3. Viet command:
   - clear graph
   - rebuild graph
   - graph stats
4. Them weighted edge:
   - `count`
   - `weight`
   - `last_interacted_at`
5. Tao query demo:
   - top interest categories cua user
   - product neighbors
   - similar users
   - query -> product path
6. Ghi tai lieu schema va cypher mau.

## Output bat buoc

- graph schema markdown
- rebuild command
- graph stats output
- 3-4 query demo

## Definition of Done

- Neo4j build graph tu data that/synthetic.
- Query tra lai ket qua dung va co y nghia.
- Co evidence ve node count va edge count.

## Evidence can nop

- Screenshot Neo4j Browser.
- Output `/graph/status`.
- Mot vai query mau va ket qua.
