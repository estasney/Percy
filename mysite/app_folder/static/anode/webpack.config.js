const ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');
var rootAssetPath = './src';
var publicPath = '/static/dist';

var path = require('path');


module.exports = {
    mode: 'development',
    entry: {
        labelApp: ['./src/js/labels.jsx'],
        projectLabelApp: ['./src/js/projectlabels.jsx']
    },
    devtool: 'inline-source-map',
    output: {
        path: path.resolve('./dist/js'),
        filename: '[name].js',
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
        new ManifestRevisionPlugin(path.join('dist', 'manifest.json'), {
            rootAssetPath: rootAssetPath,
            ignorePaths: ['/img']
        })
    ]


};


