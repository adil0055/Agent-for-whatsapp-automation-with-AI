import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/dashboard.dart';

void main() {
  runApp(const TradesBotApp());
}

class TradesBotApp extends StatelessWidget {
  const TradesBotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TradesBot',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0D0E12),
        primaryColor: const Color(0xFFFFD700), // Industrial Bumblebee Gold
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFFFD700),
          secondary: Color(0xFF262A36),
          surface: Color(0xFF14151C),
        ),
        textTheme: GoogleFonts.outfitTextTheme(ThemeData.dark().textTheme).copyWith(
          displayLarge: GoogleFonts.outfit(fontWeight: FontWeight.w700, letterSpacing: -1.2, color: Colors.white),
          titleLarge: GoogleFonts.outfit(fontWeight: FontWeight.w600, letterSpacing: -0.5, color: Colors.white),
          bodyLarge: GoogleFonts.inter(color: const Color(0xFFB0B3BC)),
          bodyMedium: GoogleFonts.inter(color: const Color(0xFF8A8F9E)),
        ),
        useMaterial3: true,
      ),
      home: const Dashboard(),
    );
  }
}
