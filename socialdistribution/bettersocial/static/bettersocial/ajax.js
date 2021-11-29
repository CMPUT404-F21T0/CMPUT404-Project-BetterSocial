// https://gist.github.com/thom-nic/1242597
// Thank this guy 10 years ago -- makes my life so much easier
// Modified for my purposes
/**
 * Node builder.  Call like:
 * $n('div',{class:'top'},'inner text') // or:
 * $n('div',{class:'top'},[$n('p',{},'nested element'])
 */
function $n(e, attrs, inner, innerHTML) {
    if (typeof (e) == 'string') e = document.createElement(e);
    if (attrs) for (let k in attrs) e.setAttribute(k, attrs[k]);
    if (inner) {
        if (typeof (inner) == 'string') e.textContent = inner;
        else if (inner.call) inner.call(e);
        else for (let i in inner) e.appendChild(inner[i]);
    }
    if (innerHTML) {
        e.innerHTML = innerHTML;
    }
    return e;
}

function renderPost(postJSON, currentUserUUID) {

    const postDiv = $n('div', {class: 'post'});

    postDiv.appendChild(renderPostHeader(postJSON));
    postDiv.appendChild(renderPostContainer(postJSON));
    postDiv.appendChild(renderPostFooter(postJSON, currentUserUUID));

    return postDiv;

}

function renderPostHeader(postJSON) {

    let header = $n('div', {class: 'post-header'});

    let leftDiv = $n(
        'div',
        {class: 'left'},
        [
            $n('a', {href: `/profile/${postJSON.author._uuid}`}, null, '<span class="iconify" data-icon="iconoir:profile-circled" data-width="42" data-height="42"></span>'),
            $n('a', {href: `/profile/${postJSON.author._uuid}`}, null, `<h3>${postJSON.author.displayName}</h3>`)
        ]
    );
    let rightDiv = $n(
        'div',
        {class: 'post-header right'},
        [$n('p', {}, '', `${new Date(postJSON.published).toLocaleString()}&nbsp;&nbsp;&nbsp;`)]
    );

    header.appendChild(leftDiv);
    header.appendChild(rightDiv);

    return header;

}

function renderPostContainer(postJSON) {

    let container = $n(
        'div',
        {class: 'post-container'},
        [
            $n(
                'a',
                {href: `/article/${postJSON._uuid}`},
                null,
                `<h2 class="post-title">${postJSON.title}</h2>
                    <h4 class="post-publisher">By: ${DOMPurify.sanitize(postJSON.author.displayName)}</h4>
                    <h4 class="post-publisher">Tags: ${(postJSON.categories && postJSON.categories.length > 0) ? postJSON.categories.join(', ') : 'N/A'}</h4>
                    <h4 class="post-publisher">Visibility: ${postJSON.visibility}</h4>
                    <p class="post-description">Description: ${DOMPurify.sanitize(postJSON.description)}</p>`
            ),
            $n('hr')
        ]
    );

    if (postJSON.contentType === 'application/base64') {
        container.appendChild($n(
            'div',
            {class: 'post-content'},
            // Super unsafe but ¯\_(ツ)_/¯
            [$n('iframe', {
                src: `data:base64, ${DOMPurify.sanitize(postJSON.content)}`,
                style: 'width: 100%; height: auto;'
            })]
        ));
    } else if (postJSON.contentType === 'text/markdown') {
        container.appendChild($n(
            'div',
            {class: 'post-content'},
            null,
            marked.parse(DOMPurify.sanitize(postJSON.content))
        ));
    } else if (postJSON.contentType === 'image/jpeg;base64' || postJSON.contentType === 'image/png;base64') {
        container.appendChild($n(
            'div',
            {class: 'image-container'},
            [$n('img', {src: `data:${postJSON.contentType}, ${postJSON.content}`})]
        ));
    } else if (postJSON.contentType === 'text/plain') {
        container.appendChild($n(
            'div',
            {class: 'post-content'},
            DOMPurify.sanitize(postJSON.content)
        ));
    } else {
        container.appendChild($n(
            'div',
            {class: 'post-content'},
            null,
            '<i>No representable content.</i>'
        ));
    }

    return container;

}

function renderPostFooter(postJSON, currentUserUUID) {

    let footer = $n('div', {class: 'post-footer right'});

    console.log(currentUserUUID.toString());
    console.log(postJSON.author._uuid.toString());
    console.log(currentUserUUID.toString() === postJSON.author._uuid.toString());

    if (currentUserUUID.toString() === postJSON.author._uuid.toString()) {

        footer.appendChild($n(
            'a',
            {class: 'icon-text', href: `/article/edit/${postJSON._uuid}`},
            'Edit'
        ));

        footer.appendChild($n(
            'a',
            {class: 'icon-text', href: `/article/${postJSON._uuid}/remove`},
            'Delete'
        ));

    }

    footer.appendChild($n(
        'a',
        {href: `/article/${postJSON._uuid}/share`},
        [$n(
            'span',
            {
                class: 'iconify',
                'data-icon': 'bi:share',
                'data-width': '30',
                'data-height': '30'
            },
        )]
    ));

    footer.appendChild($n(
        'a',
        {class: 'icon-text', href: `/article/${postJSON._uuid}/share`},
        'Share Post'
    ));

    footer.appendChild($n(
        'a',
        // TODO: Like Links
        {href: ''},
        [$n(
            'span',
            {
                class: 'iconify',
                'data-icon': 'ant-design:like-outlined',
                'data-width': '30',
                'data-height': '30'
            },
        )]
    ));

    footer.appendChild($n(
        'a',
        {class: 'icon-text', href: `/article/${postJSON._uuid}/share`},
        'Share Post'
    ));

    footer.appendChild($n(
        'a',
        {href: `/article/${postJSON._uuid}/`},
        [$n(
            'span',
            {
                class: 'iconify',
                'data-icon': 'ant-design:comment-outlined',
                'data-width': '30',
                'data-height': '30'
            },
        )]
    ));

    footer.appendChild($n(
        'a',
        {class: 'icon-text', href: `/article/${postJSON._uuid}/`},
        `${postJSON.count} Comment(s)`
    ));

    return footer;
}

function getAllPosts(currentUserUUID) {

    let localPosts = fetch('/api/posts');
    let remotePosts = fetch('/api/remote-posts');

    const streamItems = document.getElementById('stream_items');

    Promise.all([localPosts, remotePosts])
        .then(responses => {
            return Promise.all(responses.map((response => response.json())));
        }).then(arrays => {
        let fullList = [];

        arrays.forEach((array) => {
            array.forEach(post => fullList.push(post));
        });

        if (fullList.length < 1) {
            return;
        }

        fullList.sort((first, second) => {
            let firstDate = new Date(first.published);
            let secondDate = new Date(second.published);

            if (firstDate < secondDate) {
                return 1;
            }

            if (firstDate > secondDate) {
                return -1;
            }

            if (firstDate === secondDate) {
                return 0;
            }

        });

        // Clear out whatever's in there
        streamItems.innerHTML = '';

        fullList.forEach(post => {
            streamItems.appendChild(renderPost(post, currentUserUUID));
        });

    });

}

function getSinglePost(post, currentUserUUID) {

    let postView = document.getElementById('post-view');
    let renderedPost = postView.appendChild(renderPost(JSON.parse(post), currentUserUUID));

    postView.innerHTML = '';

    postView.appendChild(renderedPost);

}
