//const HtmlWebpackPlugin = require('html-webpack-plugin');
const ModuleFederationPlugin = require('webpack').container.ModuleFederationPlugin;
const path = require('path');
const ExternalTemplateRemotesPlugin = require('external-remotes-plugin');
const ConcatenatePlugin = require('./ConcatPlugin');

module.exports = {
  entry: './src/SchedulerComponent.js',
  mode: 'development',
  // mode: 'production',

  target: 'web',
  
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'main.js',
  },
  module: {
    rules: [
      {
        test: /\.jsx?$/,
        loader: 'babel-loader',
        exclude: /node_modules/,
        options: {
          presets: [
            "@babel/preset-env",
            ["@babel/preset-react", {"runtime": "automatic"}]
          ],
        },
      },
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.svg$/i,
        type: 'asset/resource',
      },
    ],
  },
  resolve: {
    fallback: {
      "fs": false,
      "path": require.resolve("path-browserify"),
      "os": require.resolve("os-browserify/browser"),
      "net": false,
    },
  },
  plugins: [
    new ModuleFederationPlugin({
      name: 'SchedulerComponent',
      filename: 'SchedulerComponent.js',
      remotes: {
        doover_home : 'doover_home@[window.dooverRemoteAccess_remoteUrl]'
      },
      exposes: {
        './SchedulerComponent': './src/SchedulerComponent',
      },
      shared: {
        react: {
          import: 'react',
          shareKey: 'react',
          shareScope: 'default',
          singleton: true,
        },
        './node_modules/react-dom': {
          singleton: true,
        },
      },
    }),
    new ConcatenatePlugin({
      source: "./dist",
      destination: "../assets",
      name: 'SchedulerComponent.js',
      ignore: 'main.js'
    }),
    new ExternalTemplateRemotesPlugin(),

    // new HtmlWebpackPlugin({
    // template: './public/index.html',
    // }),
  ],
};
