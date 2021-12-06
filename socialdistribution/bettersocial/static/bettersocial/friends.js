function showFriendListPage() {
    document.getElementById('friend-list-page').hidden = false;
    document.getElementById('friend-request-page').hidden = true;
    document.getElementById('author-list-page').hidden = true;
}

function showFriendRequestPage() {
    document.getElementById('friend-list-page').hidden = true;
    document.getElementById('friend-request-page').hidden = false;
    document.getElementById('author-list-page').hidden = true;
}

function showAuthorsPage() {
    document.getElementById('friend-list-page').hidden = true;
    document.getElementById('friend-request-page').hidden = true;
    document.getElementById('author-list-page').hidden = false;
}

// To fix some weirdness with the back button
setTimeout(() => {
    showFriendListPage();
    document.getElementById('page-friend-requests').checked = false;
    document.getElementById('page-friends').checked = true;
    document.getElementById('page-authors').checked = false;
}, 100);


