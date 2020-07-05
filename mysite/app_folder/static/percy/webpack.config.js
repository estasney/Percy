let webpack = require("webpack");
let path = require("path");

const {CleanWebpackPlugin} = require('clean-webpack-plugin');

let config = {
    module: {}
};

let jsConfig = Object.assign({}, config, {
    mode: 'production',
    entry: {
        vendor: ['./src/js/vendor.js'],
        vendor_jquery: ['./src/js/vendor_jquery.js'],
        vendor_fa: ['./src/js/vendor_fa.js'],
        vendor_d3: ['./src/js/vendor_d3.js'],
        vendor_bs_table: ['./src/js/vendor_bs_table.js'],
        vendor_moment: ['./src/js/vendor_moment.js'],
        keywords: ['./src/js/keywords.js'],
        related: ['./src/js/related.js'],
        results_table: ['./src/js/results_table.js'],
        ms_form: ['./src/js/ms_form.js'],
        d3_hist: ['./src/js/d3_hist.js']
    },
    resolve: {
        alias: {
            jquery: "jquery/src/jquery"
        }
    },
    devtool: 'source-map',
    output: {
        path: path.resolve("../assets/js"),
        filename: '[name].[hash:8].min.js'

    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: ['/node_modules/', '/img/'],
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: []
                    }
                }
            }
        ]
    },
    plugins: [
        new webpack.ProvidePlugin({
            "$": 'jquery',
            "jQuery": "jquery",
            "window.jQuery": "jquery"

        }),
        new CleanWebpackPlugin()

    ]
});

let styleConfig = Object.assign({}, config, {
    mode: "production",
    entry: {

        mainpage: ['./src/css/mainpage.css'],
        ms_form: ['./src/css/ms_form.css'],
        selectize_bootstrap: ['./src/css/selectize_bootstrap.css']
    },
    output: {
        path: path.resolve("../assets/css"),
        filename: '[name].[hash:8].css',

    },
    module: {
        rules: [
            {
                test: /\.(css)$/,
                use: {
                    loader: 'raw-loader'
                }
            }
        ]
    }

});

module.exports = [
    jsConfig, styleConfig
];


