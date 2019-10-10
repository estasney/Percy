import React from 'react';
import ReactDOM from 'react-dom';
import {IndexManager} from "./indexmanager.jsx";
import {LabelManager} from "./labelmanager.jsx";
import {DocumentManager} from "./documentmanager.jsx";
import {makeUrl} from "./utils.js";

class LabelApp extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            error: null,
            initLoaded: false,
            documentLoaded: false,
            indexLoaded: false,
            text: "",
            textAbridged: "",
            name: "",
            id: "",
            labels: [],
            sticky_state: false,
            label_hotkeys: [],
            index_docs: [],
        };
        this.shortcutKeys = this.shortcutKeys.bind(this);
        this.handleClick = this.handleClick.bind(this);
        this.handleIndexClick = this.handleIndexClick.bind(this);
        this.handleScroll = this.handleScroll.bind(this);
    }

    handleScroll(e) {
        const label_element = window.document.getElementById("sticky-label");
        const label_element_height = label_element.scrollHeight;
        const window_offset = e.srcElement.scrollingElement.scrollTop;
        if (window_offset >= label_element_height && !this.state.sticky_state) {
            this.setState({sticky_state: true});
        } else if (window_offset < label_element_height && this.state.sticky_state) {
            this.setState({sticky_state: false});
        }
    }

    shortcutKeys(e) {
        switch (e.key) {
            case "]":
                e.preventDefault();
                this.paginate("next");
                break;
            case "[":
                e.preventDefault();
                this.paginate("back");
                break;
            default:
                if (e.key in this.state.label_hotkeys) {
                    e.preventDefault();
                    const label_id = this.state.label_hotkeys[e.key];
                    this.handleClick(label_id, false);
                }
        }
    }

    componentWillUnmount() {
        window.removeEventListener('scroll', this.handleScroll);
        window.document.removeEventListener('keypress', this.shortcutKeys);
    }

    componentDidMount() {
        window.addEventListener('scroll', this.handleScroll);
        window.document.addEventListener('keypress', this.shortcutKeys);
        let params = {action: "setup"};
        let url = makeUrl(this.props.project_id, "/anode/api/label/", params);
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {

                    let hotkey2id = {};
                    result.document.labels_data.forEach(function (label) {
                        if (label.hotkey) {
                            hotkey2id[label.hotkey] = label.id;
                        }
                    });

                    this.setState({
                        initLoaded: true,
                        documentLoaded: true,
                        indexLoaded: true,
                        text: result.document.text,
                        textAbridged: result.document.text_abridged,
                        name: result.document.name,
                        id: result.document.id,
                        labels: result.document.labels_data,
                        label_hotkeys: hotkey2id,
                        index_docs: result.index
                    });
                },
                (error) => {
                    this.setState({
                        documentLoaded: false,
                        indexLoaded: false,
                        error
                    });
                }
            );

    }

    postState(doc_id, labels) {
        let url = makeUrl(this.props.project_id, "/anode/api/label/");
        fetch(url, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                doc_id_in: doc_id,
                labels: labels
            })
        })
            .then(res => res.json())
            .then(
                (result) => {
                    this.setState({
                        labels: result.document.labels_data,
                        id: result.document.id
                    });
                },
                (error) => {
                    this.setState({
                        documentLoaded: false,
                        textAbridged: error,
                        text: error,
                        name: "",
                        id: null
                    });
                }
            );

    }

    paginate(direction) {
        /*
        direction: (str) - ['back', 'next']
         */
        const doc_id = this.state.id;
        let idxDocs = this.state.index_docs.slice();
        const idxPos = idxDocs.map(function (x) {
            return x.id;
        }).indexOf(doc_id);
        const current_idx_state = idxDocs[idxPos].seen;
        if (!current_idx_state) {
            idxDocs[idxPos].seen = true;
            this.setState({
                index_docs: idxDocs
            });
        }

        this.setState({
            documentLoaded: false
        });
        let step;
        if (direction === 'next') {
            step = 1;
        } else {
            step = -1;
        }
        const next_idx_id = idxDocs[idxPos + step].id;
        let params = {action: "fetch", doc_id_in: doc_id, doc_id_out: next_idx_id};
        let url = makeUrl(this.props.project_id, "/anode/api/label/", params);
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {
                    this.setState({
                        documentLoaded: true,
                        text: result.document.text,
                        textAbridged: result.document.text_abridged,
                        name: result.document.name,
                        id: result.document.id,
                        labels: result.document.labels_data
                    });
                },
                (error) => {
                    this.setState(
                        {
                            documentLoaded: false,
                            textAbridged: error,
                            text: error,
                            name: "",
                            id: null
                        }
                    );
                }
            );
    }

    handleClick(id, active) {
        /*
        Given a label id toggle it's selection state
        Update server with new state

        id: the label id
        active: the labels current, selected state

         */
        const labels = this.state.labels.slice();
        const elementPos = labels.map(function (x) {
            return x.id;
        }).indexOf(id);
        if (active) {
            labels[elementPos].selected = !active;
        } else {
            const current_state = labels[elementPos].selected;
            labels[elementPos].selected = !current_state;
        }

        this.postState(this.state.id, labels);

    }

    handleIndexClick(id) {
        /*
        Called from Index Manager when an IndexDocument is clicked
        id: IndexDocument id

        Updates index_docs state to show seen
        Makes GET request to fetch new document
         */
        let idxDocs = this.state.index_docs.slice();
        const idxPos = idxDocs.map(function (x) {
            return x.id;
        }).indexOf(id);
        const current_idx_state = idxDocs[idxPos].seen;
        if (!current_idx_state) {
            idxDocs[idxPos].seen = true;
            this.setState({
                index_docs: idxDocs
            });
        }
        const params = {action: "fetch", doc_id_out: id, doc_id_in: this.state.id};
        const url = makeUrl(this.props.project_id, "/anode/api/label/", params);

        // Show loading
        this.setState({
            documentLoaded: false
        });
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {

                    let hotkey2id = {};
                    result.document.labels_data.forEach(function (label) {
                        if (label.hotkey) {
                            hotkey2id[label.hotkey] = label.id;
                        }
                    });

                    this.setState({
                        documentLoaded: true,
                        text: result.document.text,
                        textAbridged: result.document.text_abridged,
                        name: result.document.name,
                        id: result.document.id,
                        labels: result.document.labels_data,
                        label_hotkeys: hotkey2id,
                    });
                },
                (error) => {
                    this.setState({
                        documentLoaded: true,
                        text: error,
                        textAbridged: error,
                        name: "",
                        id: null
                    });
                }
            );

    }


    render() {
        const {
            error, initLoaded, documentLoaded, indexLoaded, text,
            textAbridged, name, id, labels, sticky_state, label_hotkeys, index_docs
        } = this.state;
        if (error) {
            return (
                <div>Error: {error.message}
                </div>
            )
        } else {
            return (
                <div className={"react-container row"}>
                    <div className={"index-container col-3"}>
                        <IndexManager
                            index_docs={this.state.index_docs}
                            parent={this}
                            loaded={indexLoaded}
                        >
                        </IndexManager>
                    </div>
                    <div className={"col-6 offset-1"}>
                        <div>
                            <LabelManager
                                labels={this.state.labels}
                                parent={this}
                                sticky_state={this.state.sticky_state}
                            >
                            </LabelManager>
                        </div>
                        <hr style={{margin: "0.8rem 0px"}}/>
                        <div className>
                            <DocumentManager
                                text={this.state.textAbridged}
                                name={this.state.name}
                                loaded={documentLoaded}
                            >
                            </DocumentManager>
                        </div>
                    </div>
                </div>
            )
        }
    }


}

// ========================================

ReactDOM
    .render(
        <LabelApp
            project_id={document.querySelector("#labelApp").dataset.projectid}
        />

        ,
        document
            .getElementById(
                'labelApp'
            ))
;





