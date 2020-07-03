const HtmlWebpackPlugin = require('html-webpack-plugin');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');
const MinifyPlugin = require("babel-minify-webpack-plugin");
var rootAssetPath = './src';
var publicPath = '/static/dist';
var webpack = require('webpack');
var path = require('path');


module.exports = {
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
        path: path.resolve('./dist/js'),
        filename: '[name].min.js',
        publicPath: publicPath
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: ['/node_modules/', '/img/'],
                use: {
                    loader: 'babel-loader',
                    options:{
                        presets: []
                    }

                }
            },
            {
                test: /\.css$/,
                loader: 'style-loader!css-loader?modules'
            },
            {
                test: /\.(img|ico)$/,
                loader: 'raw-loader'
            }
        ]
    }, plugins: [
        new webpack.ProvidePlugin({
            "$": 'jquery',
            "jQuery": "jquery",
            "window.jQuery": "jquery"

        })

    ]

};


