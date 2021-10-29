function showFriendRequestPage() {
    document.getElementById('friend-request-page').hidden = false;
    document.getElementById('friend-list-page').hidden = true;
}

function showFriendListPage() {
    document.getElementById('friend-request-page').hidden = true;
    document.getElementById('friend-list-page').hidden = false;
}

// To fix some weirdness with the back button
document.getElementById('page-friends').checked = true;
document.getElementById('page-friend-requests').checked = false;
