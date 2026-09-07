package com.silentbridge.navigation

sealed class Screen(val route: String) {
    data object Home : Screen("home")
    data object Devices : Screen("devices")
    data object Diagnostics : Screen("diagnostics")
    data object Stats : Screen("stats")
    data object ManageWords : Screen("manage_words")
}
