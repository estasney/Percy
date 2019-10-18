const ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');
var rootAssetPath = './src';
var publicPath = '/static/dist';
var webpack = require('webpack');
var path = require('path');


module.exports = {
    mode: 'development',
    entry: {
        labelApp: ['./src/js/labels.jsx'],
        projectLabelApp: ['./src/js/projectlabels.jsx'],
        vendor: ['./src/js/vendor.js']
    },
    devtool: 'inline-source-map',
    output: {
        path: path.resolve('./dist/js'),
        filename: '[name].[contenthash].js',
        publicPath: publicPath
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: ['/node_modules/', '/img/'],
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-react']
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
    },

    plugins: [
        new webpack.ProvidePlugin({
            "$": 'jquery',
            "jQuery": "jquery",
            "window.jQuery": "jquery"

        })
    ]


};


