int ping(int a) {
    return pong(a - 1);
}

int pong(int b) {
    if (b <= 0) return 0;
    return ping(b - 1);
    
    return 100; /* خطای عمدی منطقی: این کد مرده (Unreachable) است */
}