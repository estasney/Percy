import React from "react";

export class DocumentManager extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        const loaded = this.props.loaded;
        const error = this.props.error;
        if (loaded) {
            return (
                <div>
                    <h2>{this.props.name}</h2>
                    <div className={"document-text"}>
                        {this.props.text}
                    </div>
                </div>
            );
        } else if (error) {
            return (
                <div>
                    <h2>Error</h2>
                    <div className={"document-text"}>
                        error
                    </div>
                </div>
            )
        } else {
            return (
                <div>
                    <h2>Loading</h2>
                    <div className={"document-text"}>
                    </div>
                </div>
            )
        }

    }
}