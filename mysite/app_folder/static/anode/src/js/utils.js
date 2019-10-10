export function makeUrl(project_id, endpoint, params) {
    let urlString = window.origin;
    urlString += endpoint;
    urlString += project_id;
    let url = new URL(urlString);
    if (params) {
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
    }

    return url
}