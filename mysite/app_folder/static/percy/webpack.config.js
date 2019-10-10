const HtmlWebpackPlugin = require('html-webpack-plugin');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');
const MinifyPlugin = require("babel-minify-webpack-plugin");
var rootAssetPath = './src';
var publicPath = '/static/dist';
var webpack = require('webpack');
var path = require('path');


module.exports = {
    mode: 'development',
    entry: {
        vendor: ['./src/js/vendor.js'],
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
    devtool: 'inline-source-map',
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


