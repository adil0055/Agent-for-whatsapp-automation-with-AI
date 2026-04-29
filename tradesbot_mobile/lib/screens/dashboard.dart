import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'services_screen.dart';
import 'billing_screen.dart';

class Dashboard extends StatefulWidget {
  const Dashboard({super.key});

  @override
  State<Dashboard> createState() => _DashboardState();
}

class _DashboardState extends State<Dashboard> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const ServicesScreen(),
    const BillingScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      extendBody: true, // Allows content to scroll under nav bar
      bottomNavigationBar: Container(
        margin: const EdgeInsets.only(left: 24, right: 24, bottom: 32),
        decoration: BoxDecoration(
          color: const Color(0xFF14151C).withOpacity(0.9),
          borderRadius: BorderRadius.circular(30),
          border: Border.all(color: Colors.white.withOpacity(0.05)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.4),
              blurRadius: 30,
              offset: const Offset(0, 10),
            )
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem(0, LucideIcons.briefcase, 'Services'),
              _buildNavItem(1, LucideIcons.creditCard, 'Billing'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String label) {
    final isSelected = _currentIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOutCubic,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFFFD700).withOpacity(0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? const Color(0xFFFFD700) : const Color(0xFF8A8F9E),
              size: 20,
            ),
            if (isSelected) ...[
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(
                  color: Color(0xFFFFD700),
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
            ]
          ],
        ),
      ),
    );
  }
}
