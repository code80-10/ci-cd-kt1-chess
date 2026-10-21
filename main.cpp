#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#ifdef _WIN32
#include <windows.h>
#endif

bool readCoordinate(int& value) {
    std::string token;
    if (!(std::cin >> token)) return false;
    std::istringstream input(token);
    char extra;
    return static_cast<bool>(input >> value) && !(input >> extra);
}

bool between(int px, int py, int ax, int ay, int bx, int by) {
    const bool onLine = (px - ax) * (by - ay) == (py - ay) * (bx - ax);
    const bool inside = (px - ax) * (px - bx) + (py - ay) * (py - by) < 0;
    return onLine && inside;
}

int main() {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
#endif
    int kx, ky, rx, ry, bx, by;
    std::cout << "Введите координаты: король x y, ладья x y, слон x y (1..8).\n";
    if (!readCoordinate(kx) || !readCoordinate(ky) ||
        !readCoordinate(rx) || !readCoordinate(ry) ||
        !readCoordinate(bx) || !readCoordinate(by)) {
        std::cout << "Ошибка: требуется шесть целых координат.\n";
        return 1;
    }

    const auto valid = [](int x, int y) {
        return x >= 1 && x <= 8 && y >= 1 && y <= 8;
    };
    if (!valid(kx, ky) || !valid(rx, ry) || !valid(bx, by)) {
        std::cout << "Ошибка: координаты должны быть от 1 до 8.\n";
        return 1;
    }
    if ((kx == rx && ky == ry) || (kx == bx && ky == by) ||
        (rx == bx && ry == by)) {
        std::cout << "Ошибка: фигуры должны занимать разные клетки.\n";
        return 1;
    }

    const bool rookLine = kx == rx || ky == ry;
    const bool bishopLine = std::abs(kx - bx) == std::abs(ky - by);
    const bool rookThreat = rookLine && !between(bx, by, rx, ry, kx, ky);
    const bool bishopThreat = bishopLine && !between(rx, ry, bx, by, kx, ky);

    if (rookThreat && bishopThreat) {
        std::cout << "Королю угрожают чёрная ладья и чёрный слон.\n";
    } else if (rookThreat) {
        std::cout << "Королю угрожает чёрная ладья.\n";
    } else if (bishopThreat) {
        std::cout << "Королю угрожает чёрный слон.\n";
    } else {
        std::cout << "Угрозы королю нет.\n";
    }
    return 0;
}
