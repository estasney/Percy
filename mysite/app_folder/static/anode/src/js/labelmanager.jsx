import React from "react";

class InactiveLabel extends React.Component {
    constructor(props) {
        super(props);
        this.clickWrapper = this.clickWrapper.bind(this);
    }

    clickWrapper(e) {
        e.preventDefault();
        this.props.myChange(this.props.id, this.props.selected);
    }

    render() {

        if (this.props.hotkey) {
            return (

                <div className={"label-control"}>
                    <div className={"tag-group"}>
                        <a href="#" onClick={this.clickWrapper} className={"tag"}
                           style={{color: this.props.text_color, backgroundColor: this.props.bg_color}}>
                            {this.props.name}
                        </a>
                        <span>{this.props.hotkey}</span>
                    </div>


                </div>
            )
        } else {
            return (

                <div className={"label-control"}>
                    <div className={"tag-group"}>
                        <a href="#" onClick={this.clickWrapper} className={"tag"}
                           style={{color: this.props.text_color, backgroundColor: this.props.bg_color}}>
                            {this.props.name}</a>

                    </div>
                </div>
            )
        }
    }
}

class ActiveLabel extends React.Component {
    constructor(props) {
        super(props);
    }


    render() {
        if (this.props.hotkey) {
            return (
                <div className={"label-control"}>
                    <div className={"tag-group"} style={{color: this.props.text_color}}>
                    <span className={"tag"}
                          style={{backgroundColor: this.props.bg_color, color: this.props.text_color}}>
                        {this.props.name}</span>

                        <button onClick={() => this.props.myChange(this.props.id, this.props.selected)}
                                className={"close"}
                        ><span aria-hidden="true"
                               style={{
                                   backgroundColor: this.props.bg_color,
                                   color: this.props.text_color
                               }}>&times;</span>
                        </button>
                    </div>
                </div>
            )
        } else {
            return (

                <div className={"label-control"}>
                    <div className={"tag-group"} style={{color: this.props.text_color}}>
                    <span className={"tag"}
                          style={{backgroundColor: this.props.bg_color, color: this.props.text_color}}>
                        {this.props.name}</span>
                        <button onClick={() => this.props.myChange(this.props.id, this.props.selected)}
                                className={"close"}
                        ><span aria-hidden="true"
                               style={{
                                   backgroundColor: this.props.bg_color,
                                   color: this.props.text_color
                               }}>&times;</span>
                        </button>
                    </div>
                </div>
            )
        }

    }

}

export class LabelManager extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {

        const labels = this.props.labels;
        const manager = this;
        let sticky_class;
        if (this.props.sticky_state) {
            sticky_class = "sticky";
        } else {
            sticky_class = "";
        }
        const labels_list_active = labels.map(function (label) {
            if (label.selected) {
                return (<ActiveLabel
                    key={label.id}
                    selected={label.selected}
                    bg_color={label.bg_color}
                    text_color={label.text_color}
                    name={label.name}
                    hotkey={label.hotkey}
                    myChange={() => manager.props.parent.handleClick(label.id, label.selected)}
                />)
            }

        });

        const labels_list_inactive = labels.map(function (label) {

            if (!label.selected) {
                return (<InactiveLabel
                    key={label.id}
                    selected={label.selected}
                    bg_color={label.bg_color}
                    text_color={label.text_color}
                    name={label.name}
                    hotkey={label.hotkey}
                    myChange={() => manager.props.parent.handleClick(label.id, label.selected)}
                />)
            }

        });
        return (
            <div id={"sticky-label"} className={sticky_class}>
                <div className={"labels top-bar"}>
                    <button className={"pagination-btn br-top-left"}
                            onClick={() => manager.props.parent.paginate("back")}>
                        <i className="fas fa-arrow-left"></i>
                    </button>
                    <div className={"labels inactive"}>
                        {labels_list_inactive}
                    </div>
                    <button className={"pagination-btn br-top-right"}
                            onClick={() => manager.props.parent.paginate("next")}>
                        <i className="fas fa-arrow-right"></i>
                    </button>
                </div>
                <div className={"labels selected"}>
                    {labels_list_active}
                </div>
            </div>
        )
    }

}