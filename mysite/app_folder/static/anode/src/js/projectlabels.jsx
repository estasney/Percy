import React from 'react';
import {makeUrl} from "./utils.js";
import ReactDOM from "react-dom";

class LabelRow extends React.Component {
    constructor(props) {
        super(props);
        const p = this.props;
        this.state = {
            original_values: {
                name: p.name,
                bg_color: p.bg_color,
                text_color: p.text_color,
                hotkey: p.hotkey,
                active: p.active
            },
            name: this.props.name,
            id: this.props.id,
            bg_color: this.props.bg_color || "#ffff00",
            text_color: this.props.text_color || "#000000",
            hotkey: this.props.hotkey,
            is_new: this.props.is_new,
            active: this.props.active,
            name_changed: false,
            bg_color_changed: false,
            text_color_changed: false,
            hotkey_changed: false,
            active_changed: false
        };
        this.clickWrapper = this.clickWrapper.bind(this);
        this.handleInputChange = this.handleInputChange.bind(this);
        this.toggleActive = this.toggleActive.bind(this);
    }

    clickWrapper(e) {
        if (!this.state.name_changed && !this.state.bg_color_changed && !this.state.text_color_changed && !this.state.hotkey_changed && !this.state.active_changed) {
            e.preventDefault();
            return false;
        }
        this.setState({
            is_changed: false
        });
        const s = this.state;
        this.props.myChange(s);
    }

    toggleActive() {

        const new_value = !this.state.active;
        const new_active_changed = new_value !== this.state.original_values.active;

        this.setState({
            active: !this.state.active,
            active_changed: new_active_changed
        });
    }

    handleInputChange(event) {
        const target = event.target;
        const new_value = target.value;
        const name = target.name;
        // note this is async so we can't assume state is updated in time
        this.setState({
            [name]: new_value,

        });

        let k = name + "_changed";
        // check if we've returned to original values
        if (new_value === this.state.original_values[name]) {
            this.setState({
                [k]: false
            });
        } else {
            if (this.state[k] === false) {
                this.setState({
                    [k]: true
                });
            }
        }


    }

    render() {
        let savebtnClass = 'btn btn-success';
        if (!this.state.name_changed && !this.state.bg_color_changed && !this.state.text_color_changed && !this.state.hotkey_changed && !this.state.active_changed) {
            savebtnClass += " disabled";
        }
        let visibilitybtnClass = "far fa-eye";
        if (this.state.active) {
            visibilitybtnClass += "-slash";
        }
        return (
            <div className={"form-group row"}>
                <div className={"col-3"}>
                    <div className={"input-group"}>
                        <div className={"input-group-prepend"}>
                            <div className={"input-group-text"}>Name</div>
                        </div>
                        <input onChange={this.handleInputChange} name={"name"} type={"text"}
                               className={"form-control"} value={this.state.name}/>
                    </div>
                </div>
                <div className={"col-3"}>
                    <div className={"input-group"}>
                        <div className={"input-group-prepend"}>
                            <div className={"input-group-text"}>Color</div>
                        </div>
                        <input onChange={this.handleInputChange} name={"bg_color"} type={"color"}
                               className={"form-control"} value={this.state.bg_color}/>
                    </div>
                </div>
                <div className={"col-3"}>
                    <div className={"input-group"}>
                        <div className={"input-group-prepend"}>
                            <div className={"input-group-text"}>Text Color</div>
                        </div>
                        <input onChange={this.handleInputChange} name={"text_color"} type={"color"}
                               className={"form-control"} value={this.state.text_color}/>
                    </div>
                </div>
                <div className={"col-2"}>
                    <div className={"input-group"}>
                        <div className={"input-group-prepend"}>
                            <div className={"input-group-text"}>Hotkey</div>
                        </div>
                        <input onChange={this.handleInputChange} name={"hotkey"} type={"text"}
                               className={"form-control"} value={this.state.hotkey}/>
                    </div>
                </div>
                <div className={"col-1"}>
                    <div className={"input-group"}>
                        <button onClick={this.clickWrapper} className={savebtnClass}>
                            <i className={"fas fa-save"}></i>
                        </button>
                        <button onClick={this.toggleActive} className={"btn btn-secondary"}>
                            <i className={visibilitybtnClass}></i>
                        </button>
                    </div>


                </div>
            </div>

        )
    }
}

class LabelForm extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            n_empty: 0,
        };
        this.addBlankRow = this.addBlankRow.bind(this);
    }

    addBlankRow() {
        console.log("add");
        this.setState({
                n_empty: this.state.n_empty + 1
            }
        );

    }

    render() {
        const labels = this.props.labels;
        const manager = this;
        const label_rows = labels.map(function (label) {
            return (<LabelRow
                key={label.id}
                id={label.id}
                bg_color={label.bg_color}
                text_color={label.text_color}
                name={label.name}
                hotkey={label.hotkey}
                active={label.active}
                is_new={false}
                myChange={(s) => manager.props.parent.handleClick(s)}
            />)
        });

        let blank_rows = [];
        if (this.state.n_empty > 0) {
            for (let i = 0; i < this.state.n_empty; i++) {
                let chr = String.fromCharCode(97 + i);
                blank_rows.push(
                    <LabelRow
                        key={chr}
                        id={null}
                        bg_color={""}
                        name={""}
                        hotkey={""}
                        is_new={true}
                        myChange={(s) => manager.props.parent.handleClick(s)}
                    />);
            }
        }

        return (
            <div className={"labelForm col-10 offset-1"}>
                {label_rows}
                {blank_rows}
                <div className={"d-flex justify-content-center"}>
                    <button className={"btn btn-secondary"} onClick={() => this.addBlankRow()}>
                        <i className={"fas fa-plus"}></i>
                    </button>
                </div>
            </div>
        )

    }

}

//
class ProjectLabelsApp extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null,
            initLoaded: false,
            labelsLoaded: false,
            labels: [],
        };
        this.handleClick = this.handleClick.bind(this);

    }

    handleClick(label_state) {
        let url = makeUrl(this.props.project_id, "/anode/api/label/manage/");
        fetch(url, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                labels: [label_state]
            })
        }).then(res => res.json())
            .then(
                (result) => {
                    this.setState({
                        labels: result.labels
                    });
                },
                (error) => {
                    this.setState({
                        labelsLoaded: false,
                        error: error

                    });
                }
            );
    }

    componentDidMount() {
        let url = makeUrl(this.props.project_id, "/anode/api/label/manage/");
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {

                    this.setState({
                        initLoaded: true,
                        labelsLoaded: true,
                        labels: result.labels

                    });
                },
                (error) => {
                    this.setState({
                        labelsLoaded: false,
                        initLoaded: true,
                        error: error
                    });
                }
            );

    }

    render() {
        const {error, initLoaded, labelsLoaded, labels} = this.state;
        if (error) {
            return (
                <div>Error: {error.message}
                </div>
            )
        } else {
            return (
                <div className={"react-container row"}>
                    <LabelForm
                        labels={this.state.labels}
                        parent={this}
                        loaded={labelsLoaded}
                    >
                    </LabelForm>

                </div>
            )
        }
    }
}

// ========================================

ReactDOM
    .render(
        <ProjectLabelsApp
            project_id={document.querySelector("#projectLabelApp").dataset.projectid}
        />

        ,
        document
            .getElementById(
                'projectLabelApp'
            ))
;
