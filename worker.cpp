#include <iostream>
#include <string>
#include <sstream>
#include <ctime>

using namespace std;

string now() {
    time_t t = time(nullptr);
    char buf[64];
    strftime(buf, sizeof(buf), "%H:%M:%S", localtime(&t));
    return string(buf);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    cerr << "[C++ Worker] Started\n";

    string line;

    while (true) {
        if (!getline(cin, line)) {
            cerr << "[C++ Worker] Input stream closed\n";
            break;
        }

        if (line == "exit") {
            cerr << "[C++ Worker] Exit command received\n";
            break;
        }

        if (line.empty()) continue;

        stringstream ss(line);
        int value;

        if (!(ss >> value)) {
            cerr << "[C++ Worker] Invalid input: " << line << "\n";
            cout << "ERROR" << endl;
            cout.flush();
            continue;
        }

        int result = value * 2;

        cerr << "[" << now() << "] Received: " << value
            << " -> Processed: " << result << "\n";

        cout << result << endl;
        cout.flush();
    }

    cerr << "[C++ Worker] Stopped\n";
    return 0;
}