const ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');
var rootAssetPath = './src';
var publicPath = '/static/dist';
var webpack = require('webpack');
var path = require('path');


module.exports = {
    mode: 'production',
    devtool: 'source-map',
    entry: {
        labelApp: ['./src/js/labels.jsx'],
        projectLabelApp: ['./src/js/projectlabels.jsx'],
        vendor: ['./src/js/vendor.js']
    },
    output: {
        path: path.resolve('./dist/js'),
        filename: '[name].[hash:8].js',
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


