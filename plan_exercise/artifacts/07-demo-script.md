# Demo Script (Plan 07 E-commerce Integration)

Follow this step-by-step guide to demonstrate the end-to-end integration of Data, Graph, Deep Learning, and RAG Chat into the front-end E-commerce UI.

## Environment Preparation
Ensure that Docker services are running (`docker compose up -d`) and the frontend app is running (`npm run dev` in the `frontend` folder). Navigate to `http://localhost:5173`.

## Step 1: Browse and Graph Triggering
- **Action**: From the Home Page, click on a few products from the same category (e.g., Laptops).
- **Explanation**: This dispatches `product_viewed` tracking events to the backend. The backend updates the Neo4j Knowledge Graph by strengthening the user's implicit categorical interest and reinforcing the Product similarity edges.

## Step 2: Personalized Recommendation Evidence
- **Action**:
  1. Add a laptop to the Cart.
  2. Navigate to the Cart page.
- **Explanation**: The Cart Page renders a "Similar Products You May Like" section. Behind the scenes, the Application queries the Knowledge Graph's `SIMILAR_TO` edges and the RNN `model_best` predictions to rank and display the most relevant items.

## Step 3: Graph-Grounded RAG Chat 
- **Action**: 
  1. Open the Chat floating widget (bottom right corner).
  2. Send the message: *"Sản phẩm này có gì tương tự không?"*
- **Explanation**: Show the JSON debug payload (or Network tab). The AI agent leverages the RAG pipeline. The pipeline traces the Graph for neighboring nodes of the mentioned product, generating a contextual answer (highlighting `retrieval_mode=product-neighbors` and `used_graph_context=true`).

## Step 4: Real-time Fallback Chat 
- **Action**: 
  1. In the same chat, ask: *"Sản phẩm X này còn bao nhiêu cái trong kho?"*
- **Explanation**: Show the agent fetching the live stock directly from the real-time API (Cart/Order service) instead of the static Graph cache (`used_realtime_api=true`).

## Step 5: Screen Capture Deliverables
*Note: Run through this script during the presentation and capture screenshot UI views of the Search/Recommend interface, the Cart, and the detailed Chat UI state.*
