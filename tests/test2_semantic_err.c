int main() {
    return calculate(10);
}

int calculate(int n) {
    return n + y; /* خطای عمدی: متغیر y هرگز تعریف نشده است */
}

int calculate(int x) { /* خطای عمدی: نام تابع تکراری است */
    return x;
}