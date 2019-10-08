import React from "react";
import ReactDom from "react-dom";

class IndexDoc extends React.Component {
    constructor(props) {
        super(props);
        this.clickWrapper = this.clickWrapper.bind(this);
    }

    componentDidMount() {
        if (this.props.active) {

            ReactDom.findDOMNode(this).scrollIntoView({
                behavior: "smooth",
                block: "center"
            });
        }
    }

    componentDidUpdate() {
        if (this.props.active) {
            ReactDom.findDOMNode(this).scrollIntoView({
                behavior: "smooth"
            });
        }
    }


    clickWrapper(e) {
        e.preventDefault();
        this.props.myChange(this.props.id);
    }

    render() {
        let c = "index-item";
        let check = "icon";
        if (this.props.active) {
            c += " active";
        }
        if (!this.props.seen) {
            check += " hidden";
        }

        return (
            <a href="#" onClick={this.clickWrapper} className={c}>
                <span className={check}>
                    <i className={"fa fa-check"}/>
                </span>
                <span className={"snippet"}>
                    {this.props.name}
                </span>
            </a>
        )
    }

}

export class IndexManager extends React.Component {
    constructor(props) {
        super(props);
    }


    render() {
        const loaded = this.props.loaded;
        if (!loaded) {
            return (<div className={"index-list"}>
                Loading
            </div>)
        }
        let index_docs = this.props.index_docs.slice();
        const manager = this;
        const elementPos = index_docs.map(function (x) {
            return x.id;
        }).indexOf(this.props.parent.state.id);
        index_docs.forEach(function (e) {
            e.active = false;
        });

        index_docs[elementPos].active = true;
        const index_list = index_docs.map(function (doc) {
            return (
                <IndexDoc
                    key={doc.id}
                    seen={doc.seen}
                    active={doc.active}
                    name={doc.name}
                    myChange={() => manager.props.parent.handleIndexClick(doc.id)}>

                </IndexDoc>
            )

        });

        return (<div className={"index-list"}>
            {index_list}
        </div>)


    }

}