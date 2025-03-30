#include "C:\Users\HP\Downloads\Telegram Desktop\distributed-file-system\distributed-file-system\cpp\src\file_operations.cpp"
#include "C:\Users\HP\Downloads\Telegram Desktop\distributed-file-system\distributed-file-system
#include <iostream>

// Add a node to the system
void NodeManager::add_node(const std::string& ip, int port) {
    nodes.push_back({ip, port, true});
    std::cout << "Node added: " << ip << ":" << port << std::endl;
}

// Remove a node from the system
void NodeManager::remove_node(const std::string& ip, int port) {
    for (auto it = nodes.begin(); it != nodes.end(); ++it) {
        if (it->ip_address == ip && it->port == port) {
            nodes.erase(it);
            std::cout << "Node removed: " << ip << ":" << port << std::endl;
            return;
        }
    }
    std::cout << "Node not found: " << ip << ":" << port << std::endl;
}

// List all nodes
void NodeManager::list_nodes() const {
    std::cout << "Current nodes in the system:" << std::endl;
    for (const auto& node : nodes) {
        std::cout << " - " << node.ip_address << ":" << node.port
                  << (node.is_active ? " [ACTIVE]" : " [INACTIVE]") << std::endl;
    }
}

// Check if a node is active
bool NodeManager::is_node_active(const std::string& ip, int port) const {
    for (const auto& node : nodes) {
        if (node.ip_address == ip && node.port == port) {
            return node.is_active;
        }
    }
    return false;
}
