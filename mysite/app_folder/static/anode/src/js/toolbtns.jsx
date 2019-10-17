import React from "react";

export class ToolButton extends React.Component {
    constructor(props) {
        super(props);
        this.clickWrapper = this.clickWrapper.bind(this);

    }

    clickWrapper(e) {
        e.preventDefault();
        this.props.toolPressed(this.props.id);
    }

    render() {
        let btn_class = "btn btn-" + this.props.btn_class;
        let icn_class = this.props.icon;
        let btn_text = this.props.btn_text;
        let btn_active;
        if (this.props.active) {
            btn_active = " active"
        } else {
            btn_active = ""
        }
        btn_class += btn_active;
        return (
            <button
                className={btn_class}
                onClick={this.clickWrapper}
            >
                <i className={icn_class}>{btn_text}</i>
            </button>
        )

    }
}

export function FlagButton(props) {
    return (
        <ToolButton
            btn_class="info"
            icon="fas fa-bookmark"
            btn_text=" Flag"
            active={props.active}
            toolPressed={props.toolPressed}
            id={props.id}
        >

        </ToolButton>
    )
}