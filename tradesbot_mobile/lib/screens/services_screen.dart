import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:lucide_icons/lucide_icons.dart';

class ServicesScreen extends StatelessWidget {
  const ServicesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        bottom: false,
        child: CustomScrollView(
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(24, 40, 24, 30),
              sliver: SliverToBoxAdapter(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Your Services',
                      style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 36),
                    ).animate().fade(duration: 400.ms).slideY(begin: -0.2),
                    const SizedBox(height: 12),
                    Text(
                      'Define what you do so the AI can quote accurately to your customers.',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(fontSize: 16, height: 1.5),
                    ).animate().fade(delay: 100.ms, duration: 400.ms),
                  ],
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  _buildServiceCard(
                    title: 'Pipe Leak Repair',
                    price: '\$80 / hr',
                    type: 'Hourly Rate',
                    delay: 200,
                  ),
                  const SizedBox(height: 16),
                  _buildServiceCard(
                    title: 'Water Heater Install',
                    price: '\$150 base',
                    type: 'Fixed Price',
                    delay: 300,
                  ),
                  const SizedBox(height: 32),
                  GestureDetector(
                    onTap: () {
                      // Action to add service
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 20),
                      decoration: BoxDecoration(
                        border: Border.all(color: const Color(0xFF262A36), width: 2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(6),
                            decoration: const BoxDecoration(
                              color: Color(0xFF262A36),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(LucideIcons.plus, color: Colors.white, size: 16),
                          ),
                          const SizedBox(width: 12),
                          const Text(
                            'Add New Service',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    ).animate().fade(delay: 400.ms).scale(begin: const Offset(0.95, 0.95)),
                  ),
                  const SizedBox(height: 140), // Padding for bottom nav
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildServiceCard({required String title, required String price, required String type, required int delay}) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF14151C),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.04)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF262A36),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    type,
                    style: const TextStyle(
                      color: Color(0xFFB0B3BC),
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          Text(
            price,
            style: const TextStyle(
              color: Color(0xFFFFD700),
              fontSize: 22,
              fontWeight: FontWeight.w700,
              letterSpacing: -0.5,
            ),
          ),
        ],
      ),
    ).animate().fade(delay: delay.ms).slideX(begin: 0.1);
  }
}
