// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "Demo",
    products: [.library(name: "Demo", targets: ["Demo"])],
    targets: [
        .target(name: "Demo"),
        .testTarget(name: "DemoTests", dependencies: ["Demo"]),
    ]
)
