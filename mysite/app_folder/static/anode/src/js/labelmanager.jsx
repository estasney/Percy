import React from "react";
import {FlagButton} from "./toolbtns.jsx";

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
        const labeltools = this.props.labeltools;

        const labels_empty = labels.length === 0;
        const tools_empty = labeltools.length === 0;
        const loaded = !labels_empty && !tools_empty;


        if (!loaded) {
            return (
                <div id={"sticky-label"} className={""}>
                    <div className={"labels top-bar"}>
                        <button className={"pagination-btn br-top-left"}
                        >
                            <i className="fas fa-arrow-left"/>
                        </button>
                        <div className={"labels inactive"}>

                        </div>
                        <button className={"pagination-btn br-top-right"}
                        >
                            <i className="fas fa-arrow-right"/>
                        </button>
                    </div>
                    <div className={"labels selected"}>
                    </div>
                    <div className={"labels toolbar"}>
                    </div>
                </div>)
        } else {
            const manager = this;
            let sticky_class;
            if (this.props.sticky_state) {
                sticky_class = "sticky";
            } else {
                sticky_class = "";
            }

            // dont render labels where active is false - these are hidden by user
            let visible_labels = labels.filter((l) => {
                return l.active === true
            });

            const labels_list_active = visible_labels.map(function (label) {
                if (label.selected) {
                    return (<ActiveLabel
                        key={label.id}
                        selected={label.selected}
                        bg_color={label.bg_color}
                        text_color={label.text_color}
                        name={label.name}
                        hotkey={label.hotkey}
                        myChange={() => manager.props.parent.handleClick(label.id, label.selected, "label")}
                    />)
                }

            });
            const labels_list_inactive = visible_labels.map(function (label) {

                if (!label.selected) {
                    return (<InactiveLabel
                        key={label.id}
                        selected={label.selected}
                        bg_color={label.bg_color}
                        text_color={label.text_color}
                        name={label.name}
                        hotkey={label.hotkey}
                        myChange={() => manager.props.parent.handleClick(label.id, label.selected, "label")}
                    />)
                }

            });

            const flagPos = labeltools.map(function (x) {
                return x.id;
            }).indexOf("flag");
            const flagActive = labeltools[flagPos].active;
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
                    <div className={"labels toolbar"}>
                        <FlagButton
                            active={flagActive}
                            id={"flag"}
                            key={"flag"}
                            toolPressed={() => manager.props.parent.handleClick("flag", flagActive, "tool")}
                        />
                    </div>
                </div>
            )

        }
    }
}