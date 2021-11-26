function showGitActivity(githubLink) {
    let githubActivity = document.getElementById('github-activity')
    githubActivity.hidden = !githubActivity.hidden

    if (!githubActivity.hidden){
        const splitGitLink = githubLink.split('/')
        const username = splitGitLink[splitGitLink.length - 1]
        const request = new XMLHttpRequest();

        request.open("GET", `https://api.github.com/users/${username}/events/public?per_page=30`);

        request.onreadystatechange = function() { 
            if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {            
                let nodeIDs = []
                for (let event of JSON.parse(this.response)) {
                    if (event.type === "PullRequestEvent" ) {
                        const payloadPR = event.payload.pull_request
                        const nodeID = payloadPR.node_id
                        if (nodeIDs.includes(nodeID)){
                            continue
                        } else {
                            nodeIDs.push(nodeID)
                            let date = new Date(payloadPR.created_at)
                            const dateCreated = date.toLocaleString('default', {month: 'short', day: 'numeric'})
                            let div = document.createElement('div')
                            div.innerHTML = `
                                <a href=${payloadPR.html_url}>${payloadPR.title}</a>
                                <span style="float: right;"> ${dateCreated}</span>
                            `
                            githubActivity.appendChild(div)
                        }
                        
                    }
                }
            }
        }
        request.send()
    } 
    else {
        githubActivity.innerHTML = ""
    }
}