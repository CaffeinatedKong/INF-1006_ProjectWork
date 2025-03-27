// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ButtonPressAuthorization {
    address public owner;
    mapping(address => bool) public authorizedUsers;

    event ButtonPressed(address user);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "You are not the owner");
        _;
    }

    // Add an authorized user (only owner can do this)
    function addAuthorizedUser(address user) public onlyOwner {
        authorizedUsers[user] = true;
    }

    // Remove an authorized user (only owner can do this)
    function removeAuthorizedUser(address user) public onlyOwner {
        authorizedUsers[user] = false;
    }

    // Check if the user is authorized to press the button
    function isUserAuthorized(address user) public view returns (bool) {
        return authorizedUsers[user];
    }

    // Function to simulate the button press action
    function pressButton() public {
        require(authorizedUsers[msg.sender], "You are not authorized to press the button");
        emit ButtonPressed(msg.sender);  // Event emitted when button is pressed
    }
}
