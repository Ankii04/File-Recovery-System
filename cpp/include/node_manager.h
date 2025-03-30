#ifndef NODE_MANAGER_H
#define NODE_MANAGER_H

#include <string>
#include <vector>

// Structure to hold node information
struct Node {
    std::string ip_address;
    int port;
    bool is_active;
};

// NodeManager class to manage nodes in the distributed system
class NodeManager {
private:
    std::vector<Node> nodes;  // List of nodes in the system

public:
    // Adds a new node to the system
    void add_node(const std::string& ip, int port);

    // Removes a node from the system
    void remove_node(const std::string& ip, int port);

    // Lists all nodes in the system
    void list_nodes() const;

    // Checks if a node is active
    bool is_node_active(const std::string& ip, int port) const;
};

#endif // NODE_MANAGER_H
