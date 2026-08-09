import uvicorn

if __name__ == "__main__":
    print("🚀 [LocalVest Python Backend] Server đang chạy tại: http://127.0.0.1:8000")
    print("📖 [Swagger API Docs] Xem tài liệu API tự động tại: http://127.0.0.1:8000/docs")
    print("⚡ [WebSocket Live Feed] Kết nối Realtime tại: ws://127.0.0.1:8000/ws/live-feed")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
